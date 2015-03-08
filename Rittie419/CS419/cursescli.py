'''
cursescli.py
This module contains the curses CLI application for the CS419 Project
Simplifed Advising Scheduling for our implementation.
'''
import curses
import traceback
import datetime
import binascii
import sql_cmd
import db_funcs
import procfilter
import datetime
import drop_appt
import drop_calendar, send_conf_email
import mysql.connector
import curses.panel 

from mysql.connector import errorcode

# Creates and returns database connection
# @return a database connection
def create_db_connection():
    db_user = "cs419-g8"
    db_password = "9bWxwfvCAqUncYZV"
    db_host = "mysql.eecs.oregonstate.edu"
    db_database="cs419-g8"

    try:
        cnx = mysql.connector.connect(user=db_user, password=db_password, host=db_host, database=db_database)        
    except mysql.connector.Error as err:
        print "DB Connection Error"
		
    return cnx

# Queries database and returns list of appointments by email address
# @param  database connection
# @param email address of advisor
# @return list of appointments by email address
def get_appointments_list(cnx, email):
    cursor = cnx.cursor()
    query = (
        "SELECT id, student_name, appointment_date,appointment_start_time,appointment_end_time,"  
        "advisor_name, advisor_email, student_email FROM temp WHERE advisor_email = (%s)"
    ) 
    cursor.execute(query, (email,))
    data = cursor.fetchall()       
    cnx.commit()
    cursor.close()
    
    return data
    
# Display the header of the screen and receives email input from user
# @param  database connection
# @param  curses screen
# @param email address of advisor
# @return list of appointments by email address
# @return the email address of the advisor
def display_main_screen(cnx, stdscr, email):    
    error = False
    data = None
    while True:        
        stdscr.addstr("Welcome to Advisor Appointment CLI!\n\n")    
        if error:                
            stdscr.addstr("Error: no appointments found for user.\n")   
        else:
            stdscr.addstr("\n")
        email =  'chuaprar@engr.orst.edu' #delete line
        
        if email == "":
            stdscr.addstr("Type In Your OSU email: ")            
            curses.echo()
            email = stdscr.getstr(3,24,30)                                
      
        data = get_appointments_list(cnx, 'chuaprar@engr.orst.edu') # and email variable here
        rowcount = len(data)
        
        if rowcount == 0: 
            error = True
            email = ""
            stdscr.clear()
        else:
            break
    
    return data, email

# Displays the list of appointments on the screen
# @param  curses screen
# @param  list of appointments data
# @param  appointment id of appointment deleted - used to display verification of deletion
# @param  size of height of screen available to display appointments
# @param  the current row number of the selected appointment - first row is 1
# @return the current row number of the selected appointment - first row is 1
def display_appointments(stdscr, data, appt_num, lines_for_appt_display, appt_selected):
    # display appointments 
    # set highlight and normal colors
    curses.start_color()
    curses.init_pair(1,curses.COLOR_RED, curses.COLOR_WHITE)  # set colors for highlight
    h = curses.color_pair(1)   # highlight colors
    n = curses.A_NORMAL        # normal colors
    x = 1   #count the number of rows displayed, used for highlighting 
    appt_total_number = len(data)
    selected_row = appt_selected
    display_start_row = 1
    display_end_row = lines_for_appt_display
    
    # used for highlighting appointment row - stops highlight from leaving screen
    if appt_selected < 1:    # highlight will stop at first row
        selected_row = 1 
        appt_selected = 1
    elif appt_selected > lines_for_appt_display: # highlight if selected row it over display lines
        if appt_selected <= appt_total_number:
            selected_row = appt_selected                           
        elif appt_selected > appt_total_number:   # highlight will stop at last row
            selected_row = appt_total_number
            appt_selected = appt_total_number          
        display_start_row = (appt_selected - lines_for_appt_display) + 1
        display_end_row = appt_selected 
    else:
        if appt_selected > appt_total_number:     
            appt_selected -= 1 
            selected_row = appt_selected  
        else:
            selected_row = appt_selected  
    f = open('page.txt', 'a')
    f.write('total appt ' + str(appt_total_number) + ' appt selected ' + str(appt_selected) + ' selected row  ' + str(selected_row) + ' start row' + str(display_start_row) + ' end row' + str(display_end_row) +'\n') 
    f.close()
    # display verification for deleted appointment
    # if appt_num > 0:
    #    stdscr.addstr("\nAppointment " + str(appt_num) + " Has Been Deleted\n")     
    
    # display appointments
    stdscr.addstr("ID\tStudent Name\t\tAppt Date\tStart Time\tEnd Time\n")  
    for row in data:      
        row_text = str(row[0]) + "\t"   # appoint id
        row_text += row[1] + "\t"       # student name
        row_text += str(row[2]) + "\t"  # appointment date
        row_text += str(row[3]) + " \t"  # appointment start time
        row_text += str(row[4])         # appointment end time
        # display appointments only if they are withing the allowing number of rows to display
        # if x <= lines_for_appt_display:
        if display_start_row <= x <= display_end_row:
            # if the row matches the highlighted row , then highlight it
            if x == selected_row:
                stdscr.addstr(row_text + "\n", h)   
            else:
                stdscr.addstr(row_text + "\n", n) 
       
        x += 1
    stdscr.addstr('Displaying ' + str(display_start_row) + ' to ' + str(display_end_row) + ' of ' + str(appt_total_number) + ' appointments')      
    return appt_selected
 
# Gets user input -   
#   up/down arrow for selection, d for delete, q for quit, r for refresh
#   also inc or dec highlighted row if up/down arrow clicked
# @param  curses screen
# @param  the screen row number to display directions
# @param  the line number of the active row that will be highlighted
# @return user input
# @return number of appointment selected 
# @return quit was selected
def get_appointment_number(stdscr, line_start_action_input, appt_selected):   
    #get action from user
    stdscr.addstr(line_start_action_input+1,0, "Up/Down Arrow to Select | d to Delete | q to Quit | r to Refresh")   
    input = ""
    quit = False
    cursor_location = 0
    while True:
        event = stdscr.getch(line_start_action_input+2,cursor_location)
        # stdscr.addstr(str(event))    
        if event == ord("q") or event == ord("Q"): 
            input = chr(event)  
            quit = True
            break
        elif event == ord("d") or event == ord("D"): 
            input = chr(event)  
            break            
        elif event == ord("r") or event == ord("R"): 
            input = chr(event)  
            break            
        elif event == 10:
            break           
        elif event == curses.KEY_DOWN:            
            appt_selected += 1  
            break              
        elif event == curses.KEY_UP:
            appt_selected -= 1
            break  
    return input, appt_selected, quit

# Verification popup before deletion of an appointment #   
# @param  screen
# @param  the appointment number to be deleted
# @param  size of screen y axis
def verify_deletion(stdscr, appt_num, screen_y):
    # set highlight and normal colors
    curses.start_color()
    curses.init_pair(1,curses.COLOR_RED, curses.COLOR_WHITE)  # set colors for highlight
    h = curses.color_pair(1)   # highlight colors
    n = curses.A_NORMAL        # normal colors
    
    selected = 1    
    window_x = 41
    window_y = 6
    # create popup window
    window = curses.newwin(window_y,window_x,screen_y/2-window_y/2,19)
    window.addstr(1, 1, 'Do you want to delete appointment ' + str(appt_num) + '?')
    window.keypad(1) 
    window.addstr(2, window_x/2-3, "Yes", h)
    window.addstr(3, window_x/2-3, "No", n)
    curses.curs_set(0)
    window.box()
    #create panel for box put panel on top of screen
    panel1 = curses.panel.new_panel(window)        
    panel1.top(); 
    curses.panel.update_panels() 
    stdscr.refresh() 
    while True:
        event = window.getch()
        if event == curses.KEY_DOWN:            
            if selected:
                window.addstr(2, window_x/2-3, "Yes", n)
                window.addstr(3, window_x/2-3, "No", h) 
                stdscr.refresh()                 
                selected = 0
        elif event == curses.KEY_UP:
            if not selected:
                window.addstr(2, window_x/2-3, "Yes", h)
                window.addstr(3, window_x/2-3, "No", n)  
                stdscr.refresh()
                window.refresh()
                selected = 1 
        elif event == ord("y") or event == ord("Y"): 
            selected = 1
            break  
        elif event == ord("n") or event == ord("N"): 
            selected = 0
            break  
        elif event == 10:          
            break   
  
    return selected
    
    
# Gets user input 
#   up/down arrow for selection, d for delete, q for quit, r for refresh
# @param  an appointment array
def handle_drop(appointment):      
    # extract necessary data from appointment array
    db_uid = appointment[0]
    db_adv = appointment[5]
    db_adv_email = appointment[6]
    db_date = str(appointment[2])
    db_start = str(appointment[3])
    db_end = str(appointment[4])
    db_stud = appointment[1]
    db_stud_email = appointment[7]
    
    # create unique id
    uid = db_adv_email + '::' + db_date + '::' + db_start  
    
    # prepare datetime info
    dt_start = datetime.datetime.strptime(db_date + ' ' + db_start, '%Y-%m-%d %H:%M:%S')
    dt_end = datetime.datetime.strptime(db_date + ' ' + db_end, '%Y-%m-%d %H:%M:%S')
        
    # send Outlook calendar invite to advisor    
    #drop_appt.main(db_adv, db_adv_email, dt_start, dt_end)
    drop_calendar.drop_calendar(db_adv, db_stud, db_adv_email, dt_start, dt_end, uid)
    db_funcs.drop_appt_by_id(db_uid)
      
    return
        
def main():
    cnx = create_db_connection()  # create db connection for displaying list of appointments
    email = ""      # store the email used to retrieve appointments
    appt_num = 0    # appointment id of the appointment deleted used to display verification of deletion  
    appt_selected = 1  # used to keep track of which appointment row is highlighted : 1 = row one of list
    try:
        #initialize curses
        stdscr = curses.initscr()
        scrsize = stdscr.getmaxyx()
        lines_used_not_for_appt = 7
        lines_used_for_action_input = 3
        lines_for_appt_display = scrsize[0] - lines_used_not_for_appt   # number of total rows - non appt rows
        line_start_action_input = scrsize[0] - lines_used_for_action_input  #row number to start displaying input section
        #Turn off echoing of keys
        # enter cbreak mode
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(1)
        stdscr.scrollok(1)
        
        # used create app state         
        while True:
            # clear screen before drawing UI
            stdscr.clear()   
            # set appointment data to none 
            data = None
            # load top of screen includes email search
            data, email = display_main_screen(cnx, stdscr, email)
              
            # display appointments         
            appt_selected = display_appointments(stdscr, data, appt_num, lines_for_appt_display, appt_selected)  
            
            # get user command input - returns command, row number selected, if quit was selected 
            # appt_selected - function adjusts row highlighted based on up/down arrow being clicked
            input, appt_selected, quit = get_appointment_number(stdscr, line_start_action_input, appt_selected)       
          
            if not quit:
                #display input on screen - not sure if I need this
                #stdscr.addstr(input)   
                
                # check for delete input
                if input == "d" or input == 'd':
                    try:                                                           
                        appointment = data[appt_selected-1]        # get appointment data from array                
                        appt_num = int(appointment[0])             # get appointment id to delete                         
                        # show popup box to verify deletion
                        if verify_deletion(stdscr,appt_num,scrsize[0]):
                            handle_drop(appointment)       
                            appt_selected = 1     
                    except Exception as inst:                                             
                        f = open('error.txt', 'w')
                        f.write(str(inst)) 
                        f.close()
                        stdscr.deleteln()
                        stdscr.addstr(line_start_action_input+2, 10, "Invalid number")                  
            else:
                break
        
        # clean up screen and return to normal command line 
        stdscr.keypad(0)
        curses.nocbreak()
        curses.echo()
        curses.endwin()
    except:
        # In event of error, restore terminal to sane state.
        stdscr.keypad(0)
        curses.echo()
        curses.nocbreak()
        curses.endwin()
        traceback.print_exc()           # Print the exception

if  __name__ == "__main__":
    main()