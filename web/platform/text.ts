// Browser multiline controls use LF; recovered native journal helpers use CRLF.
export function win16EditText(value: string): string {
  if (typeof value !== 'string' || /[^\u0001-ÿ]/u.test(value)) {
    throw new TypeError('Original journal supports explicit one-byte NUL-free text');
  }
  const result=value.replace(/\r?\n/g,'\r\n');
  if (result.length>0x27ff) throw new RangeError('Original journal capacity exceeded');
  return result;
}

// Journal constructor NE1:b1b9 sends WM_CHAR20 after selecting the end.
// Original JPRE/JPOST saves independently demonstrate this insertion on reopen.
export function journalEditOpeningText(value: string): string {
  const text=win16EditText(value);
  if (text.length===0x27ff) throw new RangeError('Original journal insertion at capacity remains unsupported');
  return text+' ';
}
