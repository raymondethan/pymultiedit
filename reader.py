class Reader:

    def __init__(self):
        self.buffer = ""

    # no nested json allowed
    # assumes json is well-formed
    def push(self, data):
        data = data.decode()
        start_index = len(self.buffer)
        end_index = len(data) + start_index
        self.buffer += data
        output = []
        last_i = 0
        for i in range(start_index, end_index):
            if self.buffer[i] == "}":
                output.append(self.buffer[last_i:i+1])
                last_i = i+1
        self.buffer = self.buffer[last_i:]        
        return output

def test_push():
    reader = Reader()
    d_start = "{'key':'k','data':[1,2,3".encode()
    result = reader.push(d_start)
    assert (result == [])
    assert (reader.buffer == d_start.decode())

    d_middle = ",4]}{'k':2".encode()
    result = reader.push(d_middle)
    assert (result == [(d_start + d_middle[:4]).decode()])
    assert (len(reader.buffer) == len(d_middle[4:]))

    d_end = "}{'key':122342354345}".encode()
    result = reader.push(d_end)
    assert (result == [(d_middle[4:]+d_end[:1]).decode(),d_end[1:].decode()])
    assert (len(reader.buffer) == 0)

if __name__ == '__main__':
    test_push()
