#!/usr/bin/python
import mmap
import os
import struct
import subprocess
import resource
import time
class hugepage:
   def lookup_physical_address ( self ):
      page = subprocess.check_output("cat /proc/"+str(os.getpid())+"/maps | grep "+self.page_name, shell=True)
      #Example output from maps shows the virtual address range of page
      #2aaaaac00000-2aaaaae00000 rw-s 00000000 00:2b 536728                     /mnt/a
      page = page.split()[0].split('-')[0]
      vaddr = int(page,16)
      page = (vaddr / resource.getpagesize())  * 8
      pagemap = open("/proc/"+str(os.getpid())+"/pagemap", "rb")
      os.lseek(pagemap.fileno(), page, os.SEEK_SET)
      pagemap_value = struct.unpack("Q", os.read(pagemap.fileno(), 8))[0]
      #* /proc/pid/pagemap.  This file lets a userspace process find out which
         #physical frame each virtual page is mapped to.  It contains one 64-bit
         #value for each virtual page, containing the following data (from
         #fs/proc/task_mmu.c, above pagemap_read):
          #* Bits 0-54  page frame number (PFN) if present
          #* Bits 0-4   swap type if swapped
          #* Bits 5-54  swap offset if swapped
          #* Bit  55    pte is soft-dirty (see Documentation/vm/soft-dirty.txt)
          #* Bit  56    page exclusively mapped (since 4.2)
          #* Bits 57-60 zero
          #* Bit  61    page is file-page or shared-anon (since 3.5)
          #* Bit  62    page swapped
          #* Bit  63    page present
      pagemap.close()
      pagemap_value = pagemap_value & 0x007fffffffffffff
      pagemap_value = pagemap_value * resource.getpagesize()
      self.is_open = 1
      return pagemap_value
   def open_page ( self ):
      if not self.is_open :
         self.file_handle = os.open(self.page_name, os.O_RDWR, 0777)
         self.mm = mmap.mmap(self.file_handle, 0)
         dummy_read = self.mm[self.size -1]
         self.physical_address = self.lookup_physical_address()
         self.is_open = 1
   def close_page ( self ) :
      if self.is_open :
         os.close(self.file_handle)
         self.mm.close()
         self.is_open = 0
   def __init__ (self,hugetblfs_dir):
      self.is_open = 1
      if ( os.path.isfile ( hugetblfs_dir ) ) :
         #Page in hugetblfs already exists so share it
         self.original_page = 0
         self.size = 2097152;
         self.page_name = hugetblfs_dir
         self.file_handle = os.open(hugetblfs_dir, os.O_RDWR, 0777)
         self.mm = mmap.mmap(self.file_handle, 0)
         dummy_read = self.mm[self.size -1]
         self.physical_address = self.lookup_physical_address()
         #2MB pages seem to be standard
      else :
         # Set original page to show destructor that this insance created the page
         self.original_page = 1
         self.hugetblfs_dir = hugetblfs_dir
         #2MB pages seem to be standard
         self.size = 2097152;
         # Come up with a unique page name
         self.page_name = hugetblfs_dir+'/p'+str(os.getpid())+'.'+str(id(self))
         #Create file on hugetblfs
         self.file_handle = os.open(self.page_name, os.O_RDWR|os.O_CREAT, 0777)
         #Make the file the full page size
         os.ftruncate(self.file_handle,self.size)
         #mmap the file
         self.mm = mmap.mmap(self.file_handle, self.size )
         #A dummy read is necessary to update the page table for this process 
         #   with the physical address of the page
         dummy_read = self.mm[self.size-1]
         self.physical_address = self.lookup_physical_address()
   def __del__ (self):
      if self.is_open :
         os.close(self.file_handle)
         self.mm.close()
         self.is_open = 0
      #If this is not a replicated page
      if ( self.original_page ): 
         os.remove(self.page_name)
   def seek ( self, value ):
      self.mm.seek(value)
   def __getitem__(self, index):
      if isinstance (index, slice):
         if ( index.start == 'pa' ):
            return self.get_physical_address(index.stop)
         if ( index.start == 'pa_l' ):
            return self.get_physical_address(index.stop) & 0xffffffff
         if ( index.start == 'pa_u' ):
            pa_u = self.get_physical_address(index.stop)
            pa_u = pa_u >> 32
            pa_u = pa_u & 0xffffffff 
            return pa_u
         else:
            self.mm.seek(index.start)
            return struct.unpack(index.stop, self.mm.read(struct.calcsize(index.stop)))
      return self.mm[index]
   def __setitem__(self, index, value):
      self.mm.seek(index)
      self.mm.write(struct.pack(*value))
   #def __call__ ( self ):
      #return hugepage ( self.page_name )
   def get_physical_address (self, addr):
      return self.physical_address + addr
   def show_sys_info (self):
      os.system("ls -ltr "+self.hugetblfs_dir)
      os.system("grep Huge /proc/meminfo")
def show_sys_info (hugetblfs_dir):
   os.system("ls -ltr "+hugetblfs_dir)
   os.system("grep Huge /proc/meminfo")
def root_setup_hugepage (mount_dir):
   print "Must run this function as root to mount the huge pages and change permissions for all to access"
   os.system('mkdir '+mount_dir)
   os.system('mount -t hugetlbfs nodev '+mount_dir)
   os.system('chmod 0777 '+mount_dir)
   os.system('echo 512 > /proc/sys/vm/nr_hugepages')
   os.system('cat /proc/meminfo | grep Huge')
