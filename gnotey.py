#!/usr/bin/env pytho

import pygtk
import gtk
import sqlite3
import sys
import os.path
import datetime

pygtk.require("2.0")

class GNotey(object):
  def __init__(self):
      self.notedb = os.path.join( sys.path[0], 'notey.sqlite3' )
      self.setup_db()
      
      builder = gtk.Builder()
      builder.add_from_file( os.path.join( sys.path[0], "notey.xml" ) )
      builder.connect_signals(self)

      
      # GtkBuilder is not really good at treeviews
      # so we need to create our own cells and associate them
      # see http://faq.pygtk.org/index.py?req=show&file=faq13.039.htp
      # and http://zetcode.com/tutorials/pygtktutorial/advancedwidgets/
      #
      cell0 = gtk.CellRendererText()
      self.col0 = gtk.TreeViewColumn("Title", cell0,text=0)
      cell1 = gtk.CellRendererText()
      self.col1 = gtk.TreeViewColumn("Modified Date", cell1,text=1)
      self.treeview1 = builder.get_object("treeview1")
      self.treeview1.append_column(self.col0)
      self.treeview1.append_column(self.col1)      
      self.treeview1.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
      self.liststore1 = builder.get_object("liststore1")
      
      self.populate_liststore1()
      
      self.window1 = builder.get_object("window1")
      self.textbuffer1 = builder.get_object("textbuffer1")
      self.textview1 = builder.get_object("textview1")

      self.window2 = builder.get_object("window2")			
      self.entry2 = builder.get_object("entry2")

      self.entry1 = builder.get_object("entry1")
      self.vbox1 = builder.get_object("vbox1")
      self.tvsw = builder.get_object("scrolledwindow1")

      self.title = ""
      
      self.window1.show()

      
  def setup_db(self):
      if ( not os.path.isfile(self.notedb) ):
        conn = sqlite3.connect(self.notedb)
        c = conn.cursor()
        c.execute("create table notes ( title text UNIQUE, mod_date text, content text )")
        conn.commit()
        c.close()
      else:
        pass

  def responseToDialog(self,entry, dialog, response):
    dialog.response(response)
    
  def getNewTitle(self,currentTitle=""):
    dialog = gtk.MessageDialog(None,
      gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
      0,
      gtk.BUTTONS_OK,
      None)

    entry = gtk.Entry()
    entry.set_text(currentTitle)
    entry.connect("activate", self.responseToDialog, dialog, gtk.RESPONSE_OK)

    hbox = gtk.HBox()
    hbox.pack_start(gtk.Label("New title:"), False, 5, 5)
    hbox.pack_end(entry)
  
    dialog.vbox.pack_end(hbox, True, True, 0)
    dialog.show_all()

    dialog.run()
    text = entry.get_text()
    self.entry1.set_text(text)
    dialog.destroy()
    return text

  def populate_liststore1(self):
      """
populate the liststore with titles from the database
"""
      self.liststore1.clear()
      for row in self.get_note_titles():
        print "titles = %s" % row[0]
        print "date = %s" % row[1]
        self.liststore1.append((row[0],))

  def search_title_populate_liststore1(self,title):
      """
populate the liststore with titles from the database
"""
      self.liststore1.clear()
      for row in self.get_note_titles(title):
        print "titles = %s" % row[0]
        print "date = %s" % row[1]
        self.liststore1.append((row[0],))
    
  
  def get_note_titles(self,title=""):
      """
get the title from our sqlite3 database self.notedb
"""
      if not title:
        conn = sqlite3.connect(self.notedb)
        c = conn.cursor()
        c.execute("select title,mod_date from notes order by title")
        row = c.fetchall()
        c.close()
      else:
        conn = sqlite3.connect(self.notedb)
        c = conn.cursor()
        c.execute("select title,mod_date from notes where title like ?",(title + "%",))
        row = c.fetchall()
        c.close()
      return row


  def get_curr_date(self):
        now = datetime.datetime.now()
        curr_date = now.strftime("%Y-%m-%d %H:%M")
        return curr_date
      
  def get_note_content(self, title=""):
      """
      Give a title get the content of a note from self.notedb
      """
      if not title:
        return ""
      else:
        conn = sqlite3.connect(self.notedb)
        c = conn.cursor()
        c.execute("select content from notes where title = ?", (title,))
        rows = c.fetchall()
        if rows != [] :
          content = rows[0][0]
          c.close()
          return content
        else:
          c.close()
          raise Exception("Empty note")
  
  def create_new_note(self, title, content=""):
      if title:
        
        conn = sqlite3.connect(self.notedb)
        c = conn.cursor()

        mod_date = self.get_curr_date()
        
        c.execute("insert into notes values (?, ?, ?)", (title,mod_date,content))
        conn.commit()
        c.close()
        self.populate_liststore1()
      else:
        pass

  def delete_note(self):
      if self.title:
        conn = sqlite3.connect(self.notedb)
        c = conn.cursor()
        c.execute("delete from notes where title = ?", (self.title,))
        conn.commit()
        c.close()
      else:
        pass

  def edit_title(self,newtitle):
      if self.title:
        conn = sqlite3.connect(self.notedb)
        c = conn.cursor()
        c.execute("update notes set title = ? where title = ?", (newtitle, self.title))
        conn.commit()
        c.close()
    
       
  def on_window1_destroy(self,widget,data=None):
      self.save_note()
      gtk.main_quit()

 
  def on_treeview1_row_activated(self, widget, row, col):
      """
      When a title is selected update the textbuffer with its contents
      """
      model = widget.get_model()
      title = model[row][0]
      try:
        content = self.get_note_content(title)
      except Exception as e:
        content = ""
      self.title = title
      self.textbuffer1.set_text(content)
      self.entry1.set_text(self.title)
  
  def treeview1_select_title(self, title):
      model = self.treeview1.get_model()
      i = 0
      for x in model:
        if x[0] == title:
          break
        else:
          i += 1
      if i <= len(model):
        self.treeview1.set_cursor((i,))
      else:
        pass

  def on_treeview1_key_release_event(self,widget,event):

      treeselection = widget.get_selection()
      model, rows = treeselection.get_selected_rows()
      """
      Store selected titles to list
      """
      titles = []
      for j in rows:
        titles.append(model[j][0])
      
      """
      Edit of Titles
      """
      if len(titles) == 1:
        title = titles[0]
        self.title = title
        keyname = gtk.gdk.keyval_name(event.keyval)
        if event.keyval == 65471:
          newtitle = self.getNewTitle(title)          
          if newtitle:
            self.edit_title(newtitle)
            self.title = newtitle
            self.populate_liststore1()
            self.treeview1_select_title(newtitle)
            content = self.get_note_content(newtitle)
            self.textbuffer1.set_text(content)
            self.textview1.grab_focus()

      """
      Deletion of Titles
      """
      for title in titles:
        self.title = title
        keyname = gtk.gdk.keyval_name(event.keyval)
        #print "Key %s (%d) was pressed" % (keyname, event.keyval)
        if event.keyval == 65535:
          self.delete_note()
          self.populate_liststore1()
          self.entry1.set_text("")
                

  
  def on_entry1_activate(self, widget, data=None):
      """
      When text entry is activate [ i.e enter pressed ] either
      * Open existing note, or
      * Create a new note
      """
      title = widget.get_text()
      if title:
        try:
          content = self.get_note_content(title)
        except Exception as e:
          self.create_new_note(title, "")
          content=""
        self.title = title
        self.treeview1_select_title(title)
        self.textbuffer1.set_text(content)
        self.textview1.grab_focus()
    
  def on_entry1_focus_in_event(self, widget, direction, data=None):
      """
      """
      if self.tvsw.get_parent() == None :
        self.vbox1.pack_start(self.tvsw)
      else:
        pass

  def on_entry1_key_release_event(self,widget,event):
    """
    Implementing incremental search
    """
    
    keyname = gtk.gdk.keyval_name(event.keyval)
    #print "Key %s (%d) was pressed" % (keyname, event.keyval)
    self.liststore1.clear()
    title = widget.get_text()
    self.search_title_populate_liststore1(title)
    if title == "":
      self.populate_liststore1()
    pass

    
  def save_note(self):
      if self.title:
        conn = sqlite3.connect(self.notedb)
        c = conn.cursor()
        content = self.textbuffer1.get_text(
                    self.textbuffer1.get_start_iter(),
                    self.textbuffer1.get_end_iter())
        mod_date = self.get_curr_date()
        c.execute("update notes set content = ?,mod_date = ? where title = ?", (content,mod_date,self.title))
        conn.commit()
        c.close()
      else:
        pass
      
  def on_textview1_focus_out_event(self, widget, data=None):
      self.save_note()
  
if __name__ == "__main__":
  app = GNotey()
  gtk.main()

