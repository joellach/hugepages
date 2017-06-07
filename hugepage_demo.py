#!/usr/bin/python
from hugepage import *
show_sys_info ( '/tmp/hugepage_mnt' )
# Create a huge page in the /tmp/hugepage_mnt hugetblfs
hugepage_a = hugepage('/tmp/hugepage_mnt')
#This is what a 32 Byte XCB write looks like
print "Location 0x300 initial value in hugepage: "+hex(hugepage_a[0x300:'I'][0])
print "Physical address of the 2MB huge page: "+hex(hugepage_a['pa':0x0])
hugepage_a[0x300] = 'QQQQ' , 0xababcdcd34345555 , 0x900900009, 0x300060007, 0xfaaaaaaaf
print "Location 0x300 value in hugepage: "+hex(hugepage_a[0x300:'I'][0])
