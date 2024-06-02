from pathlib import Path
import sys
sys.path.insert(0, 'include')

from anb_pack import ANBPack
from anb_unpack import ANBUnpack    
    
if __name__ == '__main__':
    if len(sys.argv) != 2: 
        print("Error: Please specify a target .anb file or directory to pack.")
        exit()
    filename = sys.argv[1]
    if Path(filename).is_file():
        ANBUnpack(filename)
    else:
        ANBPack(filename)