# hugepages
Example of using huge pages in Python and looking up the physical address in the page table for DMA access
   -hugepage_demo.py  
      -Demonstrates the usage of the hugepage class
   -hugepage.py
      -The hugepage class aquires a tempororary huge page, looks up the physical address, and provides access functions
   -root_setup.py
      -Run this script as root to set up huge pages on the system
