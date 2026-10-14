import struct
import unittest
from tools.yukontree import TreeError, decode_normalized, select_linda_initial_record, step_choice_links, open_linda_dialogue


def record(text=b'', word0=0, link=0, action=(0,0,0,0), condition=(0,0), voice=0):
    return struct.pack('<9H',word0,link,*action,*condition,voice)+text+b'\0'+bytes(255-len(text))


def tree(*records):
    return struct.pack('<HH',4,len(records))+b''.join(records)


class TreeTests(unittest.TestCase):
    def test_original_depth_first_structure_preserves_metadata(self):
        payload=tree(record(b'override',condition=(2,1),voice=3400),record(),
                     record(b'hello',voice=3401),record(b'yes',link=1,action=(240,4,500,0)),
                     record(b' '),record(),record(),record())
        result=decode_normalized(payload)
        self.assertEqual((result.speaker_word,result.count_word),(4,8))
        self.assertEqual(result.initial_overrides[0].condition,(2,1))
        self.assertEqual(result.root.record.offset,0x228)
        choice=result.root.choices[0]
        self.assertEqual((choice.record.link_word,choice.record.action),(1,(240,4,500,0)))
        self.assertEqual(choice.response.record.text,b' ')
        self.assertEqual(choice.response.choices,())
        self.assertEqual(result.trailing_empty_offsets,(4+7*274,))

    def test_linda_initial_override_requires_explicit_raw_flag(self):
        source=decode_normalized(tree(record(b'override',condition=(2,1)),record(),record(b'root'),record()))
        self.assertEqual(select_linda_initial_record(source,0).text,b'root')
        for flag in (1,32768,65535):
            self.assertEqual(select_linda_initial_record(source,flag).text,b'override')
        with self.assertRaises(TreeError):
            select_linda_initial_record(source,-1)

    def test_linda_selects_before_marking_seen(self):
        source=decode_normalized(tree(record(b'override',condition=(2,1),voice=3400),record(),record(b'root',voice=3401),record()))
        self.assertEqual(tuple((r.voice_id,w) for r,w in (open_linda_dialogue(source,0,0),open_linda_dialogue(source,1,0),open_linda_dialogue(source,0,1))),((3401,1),(3400,1),(3401,0)))
        with self.assertRaises(TreeError):open_linda_dialogue(source,0,65536)

    def test_original_forward_and_absolute_exit_links(self):
        source=decode_normalized(tree(record(),record(b'root'),record(b'partner',link=2),
                                     record(b'agreed'),record(b'confirm',link=1,action=(240,4,500,0)),
                                     record(b' '),record(),record(),record()))
        first=step_choice_links(source,(),frozenset(),0,1)
        self.assertEqual(first.next_path,(0,))
        self.assertEqual(first.response_record.text,b'agreed')
        last=step_choice_links(source,first.next_path,first.visited_offsets,0,1)
        self.assertIsNone(last.next_path)
        self.assertEqual(last.selected_record.action,(240,4,500,0))
        self.assertEqual(last.response_record.text,b' ')

    def test_action_failure_keeps_forward_link_at_current_node(self):
        source=decode_normalized(tree(record(),record(b'root'),record(b'choice',link=2),
                                     record(b'reply'),record(b'back',link=1),record(b' '),record(),record(),record()))
        result=step_choice_links(source,(),frozenset(),0,0)
        self.assertEqual(result.next_path,())
        self.assertIsNone(result.response_record)

    def test_forward_native_first_child_response_rule(self):
        source=decode_normalized(tree(record(),record(b'root'),record(b'leaf',link=2),
                                     record(b'reply'),record(),record(b'branch',link=2),
                                     record(b'child'),record(b'back',link=1),record(b' '),record(),record(),record()))
        self.assertEqual(step_choice_links(source,(),frozenset(),0,1).next_path,())
        visited=frozenset(c.record.offset for c in source.root.choices[1].response.choices)
        self.assertEqual(step_choice_links(source,(),visited,1,1).next_path,(1,))

    def test_choice_without_response_uses_empty_record(self):
        result=decode_normalized(tree(record(),record(b'root'),record(b'choice'),record(),record()))
        self.assertIsNone(result.root.choices[0].response)

    def test_nonzero_trailing_record_fails(self):
        with self.assertRaises(TreeError):
            decode_normalized(tree(record(),record(b'root'),record(),record(b'extra')))

    def test_bad_lengths_counts_and_unterminated_strings_fail(self):
        good=tree(record(),record(b'root'),record())
        bad_count=bytearray(good);struct.pack_into('<H',bad_count,2,2)
        bad_text=bytearray(good);bad_text[4+274+18:4+2*274]=b'x'*256
        for payload in (b'',good[:-1],bytes(bad_count),bytes(bad_text)):
            with self.assertRaises(TreeError):
                decode_normalized(payload)

    def test_missing_nested_terminator_fails(self):
        with self.assertRaises(TreeError):
            decode_normalized(tree(record(),record(b'root'),record(b'choice'),record(b'reply')))

    def test_more_than_ten_choice_slots_fails(self):
        records=[record(),record(b'root')]
        for i in range(11):
            records.extend([record(str(i).encode()),record()])
        records.append(record())
        with self.assertRaises(TreeError):
            decode_normalized(tree(*records))
