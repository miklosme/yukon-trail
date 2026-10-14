import struct,unittest
from tools.audit_trees import inspect_graph,root_from_source

def record(text=b'',voice=0,action=(0,0,0,0),condition=(0,0),link=0):
    return struct.pack('<9H',0,link,*action,*condition,voice)+text+b'\0'+bytes(255-len(text))

class GraphCensus(unittest.TestCase):
    def test_actual_record_roles_and_reference_inventory(self):
        records=[record(b'override',voice=123,condition=(2,1)),record(),
                 record(b'root',voice=456),record(b'choice',action=(250,251,80,0),link=1),
                 record(),record(),record()]
        result=inspect_graph(struct.pack('<2H',16,len(records))+b''.join(records))
        self.assertEqual(result['status'],'parsed')
        self.assertEqual((result['initial_override_count'],result['response_nodes'],result['choice_records']),(1,1,1))
        self.assertEqual([r['offset']for r in result['records']],[4,552,826])
        self.assertEqual([r['voice_id']for r in result['records']],[123,456,0])
        self.assertEqual(result['records'][2]['action_words'],[250,251,80,0])
        self.assertEqual(result['records'][0]['condition_words'],[2,1])
        self.assertEqual(result['trailing_empty_offsets'],[1648])
        self.assertNotIn('text',result['records'][0])
        self.assertEqual(root_from_source(struct.pack('<2H',16,len(records))+b''.join(records)),552)

    def test_unsupported_graph_is_retained_as_failure(self):
        self.assertEqual(inspect_graph(b'\0\0')['status'],'unsupported')
        rows=[record(),record(b'root'),record(),record(b'unexpected')]
        result=inspect_graph(struct.pack('<2H',0,4)+b''.join(rows))
        self.assertEqual(result['status'],'unsupported')
        self.assertIn('Nonzero trailing',result['reason'])

    def test_independent_sentinel_root_rejects_missing_bounds(self):
        for data in (b'\0\0',struct.pack('<2H',0,0),struct.pack('<2H',0,1)+record(),
                     struct.pack('<2H',0,1)+record(b'no terminator')):
            with self.assertRaises(ValueError):root_from_source(data)
