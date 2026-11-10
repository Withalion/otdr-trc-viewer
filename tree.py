import struct,sys
from dec import stream
B=16
def node(buf,h):
    end,typ,size,ptr=struct.unpack_from('<4I',buf,h)
    data=buf[ptr+B:ptr+B+size]
    st=ptr+B+size
    name=buf[st:buf.index(b'\0',st)].decode('latin1')
    return name,typ,size,data
def walk(buf,h,depth=0,path='',out=None,show=True):
    name,typ,size,data=node(buf,h)
    p=path+'/'+name
    if out is not None: out[p]=(typ,data)
    if typ==0:
        kids=struct.unpack(f'<{size//4}I',data)
        if show: print('  '*depth+f'{name}/')
        for k in kids:
            if k: walk(buf,k+B,depth+1,p,out,show)
        return
    if typ==1 and size==4: val=struct.unpack('<i',data)[0]
    elif typ==3 and size==8: val=struct.unpack('<d',data)[0]
    elif typ==2 and size==16: val=data.hex()
    else: val=f'<t{typ} {size}B> '+repr(data[:32])
    if show: print('  '*depth+f'{name} = {val}')
def load(fn):
    buf=stream(fn); out={}
    walk(buf,0x49,out=out,show=False); return out
if __name__=="__main__":
    buf=stream(sys.argv[1]); walk(buf,0x49)
