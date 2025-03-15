#!/usr/bin/env python3
import curses
import json
import curses.textpad
from pathlib import Path
import time
from datetime import datetime
import sys
import argparse

CONFIG_PATH = Path.home() / ".impulse_control.json"

class ImpulseControlApp:
    def __init__(self, curses_scr):
        self.stdscr = curses_scr
        self.goals = {}
        self.current_goal = None
        self.current_state = 'menu'
        self.selected_index = 0
        self.textbox = None
        self.goal_to_delete = None
        self.status_message = None
        self.status_time = 0
        self.header_win = None
        self.content_win = None
        self.footer_win = None
        self.app_version = "v1.1.0"
        
        self.init_colors()
        self.load_data()
        self.setup_window()
        self.create_layout()
        self.run()

    def init_colors(self):
        curses.start_color()
        curses.use_default_colors()
        # Modern color scheme
        curses.init_pair(1, curses.COLOR_GREEN, -1)     # Success / positive
        curses.init_pair(2, curses.COLOR_YELLOW, -1)    # Warnings / help text
        curses.init_pair(3, curses.COLOR_RED, -1)       # Error / alert
        curses.init_pair(4, curses.COLOR_CYAN, -1)      # Info / highlight
        curses.init_pair(5, curses.COLOR_BLUE, -1)      # Secondary info
        curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_BLUE)  # Selected item
        curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_WHITE) # Header
        curses.init_pair(8, curses.COLOR_WHITE, curses.COLOR_GREEN) # Success banner
        curses.init_pair(9, curses.COLOR_BLACK, curses.COLOR_CYAN)  # Info banner

    def setup_window(self):
        curses.curs_set(0)  # Hide cursor
        self.stdscr.keypad(True)  # Enable special keys
        self.stdscr.timeout(500)  # Longer timeout to reduce flicker
        
    def create_layout(self):
        """Create a modern 3-panel layout with header, content, and footer"""
        h, w = self.stdscr.getmaxyx()
        
        # Create header (1 line), content (h-3 lines), footer (2 lines)
        self.header_win = curses.newwin(1, w, 0, 0)
        self.content_win = curses.newwin(h-3, w, 1, 0)
        self.footer_win = curses.newwin(2, w, h-2, 0)
        
        # Enable keypad for all windows
        self.header_win.keypad(True)
        self.content_win.keypad(True)
        self.footer_win.keypad(True)
    
    def draw_chrome(self):
        """Draw common UI chrome (header, borders, etc.)"""
        h, w = self.stdscr.getmaxyx()
        
        # Draw header
        self.header_win.clear()
        self.header_win.bkgd(' ', curses.color_pair(7))
        header_text = " ImpulseCheck "
        version_text = self.app_version
        self.header_win.addstr(0, 0, header_text, curses.A_BOLD)
        self.header_win.addstr(0, w - len(version_text) - 1, version_text)
        self.header_win.refresh()
        
        # Set background for other windows
        self.content_win.clear()
        self.footer_win.clear()
        
        # Draw footer border
        self.footer_win.hline(0, 0, curses.ACS_HLINE, w)
        self.footer_win.refresh()

    def load_data(self):
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, 'r') as f:
                    data = json.load(f)
                    self.goals = data.get('goals', {})
            except json.JSONDecodeError:
                self.goals = {}
        if not self.goals:
            self.current_state = 'create_goal'

    def save_data(self):
        with open(CONFIG_PATH, 'w') as f:
            json.dump({'goals': self.goals}, f)

    def run(self):
        last_state = None
        while True:
            # Check if we need to clear status message
            if self.status_message and time.time() - self.status_time > 3:
                self.status_message = None
                self.draw_status()
                
            # Only redraw if the state has changed or if we're in a state that needs constant updates
            if self.current_state != last_state or self.current_state in ['menu']:
                # Draw common UI elements
                self.draw_chrome()
                
                # Draw state-specific UI
                if self.current_state == 'menu':
                    self.draw_menu()
                elif self.current_state == 'view_goal':
                    self.draw_goal()
                elif self.current_state == 'create_goal':
                    self.draw_create_goal()
                elif self.current_state == 'delete_confirm':
                    self.draw_delete_confirm()
                
                last_state = self.current_state
            
            # Handle input for the current state
            if self.current_state == 'menu':
                self.handle_menu_input()
            elif self.current_state == 'view_goal':
                self.handle_goal_input()
            elif self.current_state == 'create_goal':
                self.handle_create_goal()
                last_state = None  # Force redraw after creation
            elif self.current_state == 'delete_confirm':
                self.handle_delete_confirm()

    # Menu state functions
    def draw_menu(self):
        h, w = self.content_win.getmaxyx()
        help_text = "[C]Create   [↑↓]Move   [D]Delete   [Q]Quit   [Enter]Open"
        
        # Draw title centered with decorative borders
        title = " Goals "
        title_x = (w - len(title)) // 2
        self.content_win.addstr(1, title_x - 15, "─" * 14, curses.color_pair(4))
        self.content_win.addstr(1, title_x, title, curses.color_pair(4) | curses.A_BOLD)
        self.content_win.addstr(1, title_x + len(title), "─" * 14, curses.color_pair(4))
        
        # Draw goals list with a box around it
        if self.goals:
            # Draw box around the goals list
            self.content_win.attron(curses.color_pair(5))
            self.content_win.box()
            self.content_win.attroff(curses.color_pair(5))
            
            # Goal list headers
            header_y = 3
            self.content_win.addstr(header_y, 2, "Goal Name", curses.A_BOLD)
            self.content_win.addstr(header_y, w - 10, "Count", curses.A_BOLD)
            self.content_win.hline(header_y + 1, 1, curses.ACS_HLINE, w - 2)
            
            # Goals
            start_y = header_y + 2
            for idx, goal in enumerate(self.goals.keys()):
                counter = self.goals[goal]['counter']
                
                # Highlight selected row
                if idx == self.selected_index:
                    # Fill the entire row with the highlight color
                    self.content_win.hline(start_y + idx, 1, ' ', w - 2, curses.color_pair(6))
                    self.content_win.addstr(start_y + idx, 2, goal, curses.color_pair(6) | curses.A_BOLD)
                    self.content_win.addstr(start_y + idx, w - 10, f"{counter}", curses.color_pair(6) | curses.A_BOLD)
                else:
                    # Normal row
                    self.content_win.addstr(start_y + idx, 2, goal)
                    
                    # Color counter based on value
                    count_color = curses.color_pair(1)  # Default green
                    self.content_win.addstr(start_y + idx, w - 10, f"{counter}", count_color)

        # Empty state message
        if not self.goals:
            empty_msg = "✧ No goals found ✧"
            hint_msg = "Press C to create your first goal!"
            
            self.content_win.addstr(h//2 - 1, (w-len(empty_msg))//2, empty_msg, curses.color_pair(3) | curses.A_BOLD)
            self.content_win.addstr(h//2 + 1, (w-len(hint_msg))//2, hint_msg, curses.color_pair(4))

        # Current date in footer
        date_str = datetime.now().strftime("%A, %B %d, %Y")
        self.footer_win.addstr(1, w - len(date_str) - 1, date_str, curses.color_pair(5))

        # Help text in footer
        self.footer_win.addstr(1, 1, help_text, curses.color_pair(2))
        
        # Refresh windows
        self.content_win.refresh()
        self.footer_win.refresh()

    def handle_menu_input(self):
        try:
            key = self.stdscr.getch()
            if key == -1:
                return

            if key == curses.KEY_UP:
                self.selected_index = max(0, self.selected_index - 1)
                self.set_status(f"Selected: {list(self.goals.keys())[self.selected_index]}")
            elif key == curses.KEY_DOWN:
                self.selected_index = min(len(self.goals)-1, self.selected_index + 1)
                if self.goals:
                    self.set_status(f"Selected: {list(self.goals.keys())[self.selected_index]}")
            elif key in [10, 13] and self.goals:  # Enter key
                self.current_goal = list(self.goals.keys())[self.selected_index]
                self.current_state = 'view_goal'
                self.set_status(f"Viewing goal: {self.current_goal}")
            elif key in [ord('c'), ord('C')]:
                self.current_state = 'create_goal'
                self.set_status("Creating new goal...")
            elif key in [ord('d'), ord('D')] and self.goals:
                self.goal_to_delete = list(self.goals.keys())[self.selected_index]
                self.current_state = 'delete_confirm'
            elif key in [ord('q'), ord('Q')]:
                self.set_status("Saving and quitting...", error=False)
                raise KeyboardInterrupt
            # Easter egg
            elif key in [ord('?')]:
                self.set_status("👋 Remember: each step matters!", error=False)
        except KeyboardInterrupt:
            self.quit()

    # Goal viewing state functions
    def draw_goal(self):
        h, w = self.content_win.getmaxyx()
        data = self.goals[self.current_goal]
        help_text = "[I]Increment   [U]Undo   [M]Menu   [Q]Quit"
        
        # Clear content area
        self.content_win.clear()
        
        # Draw a decorative border
        self.content_win.attron(curses.color_pair(5))
        self.content_win.box()
        self.content_win.attroff(curses.color_pair(5))
        
        # Draw goal name at the top
        goal_title = f" {self.current_goal} "
        title_x = (w - len(goal_title)) // 2
        
        # Draw a fancy header with the goal name
        self.content_win.addstr(1, title_x - 10, "╭" + "─" * 8, curses.color_pair(4))
        self.content_win.addstr(1, title_x, goal_title, curses.color_pair(4) | curses.A_BOLD)
        self.content_win.addstr(1, title_x + len(goal_title), "─" * 8 + "╮", curses.color_pair(4))
        
        # Display counter in a box in the center with a large font effect
        count_y = h // 2 - 4
        count = str(data['counter'])
        count_x = (w - len(count) * 3) // 2
        
        # Draw a highlight box around the counter
        box_width = len(count) * 4
        box_height = 5
        box_x = count_x - 2
        box_y = count_y - 1
        
        # Draw the counter box with rounded corners
        self.content_win.addch(box_y, box_x, curses.ACS_ULCORNER)
        self.content_win.addch(box_y, box_x + box_width, curses.ACS_URCORNER)
        self.content_win.addch(box_y + box_height, box_x, curses.ACS_LLCORNER)
        self.content_win.addch(box_y + box_height, box_x + box_width, curses.ACS_LRCORNER)
        
        for i in range(1, box_width):
            self.content_win.addch(box_y, box_x + i, curses.ACS_HLINE)
            self.content_win.addch(box_y + box_height, box_x + i, curses.ACS_HLINE)
            
        for i in range(1, box_height):
            self.content_win.addch(box_y + i, box_x, curses.ACS_VLINE)
            self.content_win.addch(box_y + i, box_x + box_width, curses.ACS_VLINE)
        
        # Draw large counter digits with simple ASCII art
        for i, digit in enumerate(count):
            digit_x = count_x + i * 4
            self.content_win.addstr(count_y, digit_x, digit, curses.color_pair(1) | curses.A_BOLD)
            
        # Show motivational message
        motivation_y = box_y + box_height + 2
        motivation = "Focus on your resolution!"
        self.content_win.addstr(motivation_y, (w - len(motivation)) // 2, motivation, 
                           curses.color_pair(4) | curses.A_ITALIC)
        
        # Show last updated timestamp
        if 'last_updated' in data:
            updated_str = f"Last updated: {data['last_updated']}"
            self.content_win.addstr(h - 3, (w - len(updated_str)) // 2, updated_str, 
                              curses.color_pair(5))
        
        # Help text in footer
        self.footer_win.move(1, 0)
        self.footer_win.clrtoeol()
        self.footer_win.addstr(1, 1, help_text, curses.color_pair(2))
        
        # Refresh windows
        self.content_win.refresh()
        self.footer_win.refresh()

    def handle_goal_input(self):
        key = self.stdscr.getch()
        if key == -1:
            return
        
        need_redraw = False
        data = self.goals[self.current_goal]
        if key in [ord('i'), ord('I')]:
            data['history'].append(data['counter'])
            data['counter'] +=1
            data['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save_data()
            need_redraw = True
            self.set_status(f"Counter increased to {data['counter']}")
        elif key in [ord('u'), ord('U')] and data['history']:
            data['counter'] = data['history'].pop()
            data['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save_data()
            need_redraw = True
            self.set_status(f"Counter reset to {data['counter']}")
        elif key in [ord('m'), ord('M')]:
            self.current_goal = None
            self.current_state = 'menu'
            self.set_status("Returned to menu")
        elif key in [ord('q'), ord('Q')]:
            self.set_status("Saving and quitting...", error=False)
            self.quit()
        # Easter egg
        elif key in [ord('?')]:
            motivational_messages = [
                "Every count is a step toward your goal!",
                "Small steps lead to big changes!",
                "Consistency is key to success!",
                "You're doing great, keep going!",
                "Progress, not perfection!"
            ]
            import random
            self.set_status(f"👋 {random.choice(motivational_messages)}", error=False)
            
        # Only redraw when the counter changes
        if need_redraw:
            self.draw_goal()

    # Creation state functions
    def draw_create_goal(self):
        h, w = self.content_win.getmaxyx()
        prompt = "New goal name (ESC to cancel):"
        help_text = "Press Enter when done | ESC to cancel"
        
        # Clear content area
        self.content_win.clear()
        
        # Draw fancy title
        title = " Create New Goal "
        title_x = (w - len(title)) // 2
        
        self.content_win.addstr(1, title_x - 10, "┌" + "─" * 8, curses.color_pair(5))
        self.content_win.addstr(1, title_x, title, curses.color_pair(5) | curses.A_BOLD)
        self.content_win.addstr(1, title_x + len(title), "─" * 8 + "┐", curses.color_pair(5))
        
        # Draw form box
        form_y = 4
        form_height = 5
        form_width = w - 10
        form_x = 5
        
        # Draw the form box
        self.content_win.attron(curses.color_pair(4))
        for i in range(form_width):
            self.content_win.addch(form_y, form_x + i, curses.ACS_HLINE)
            self.content_win.addch(form_y + form_height, form_x + i, curses.ACS_HLINE)
        
        for i in range(form_height):
            self.content_win.addch(form_y + i, form_x, curses.ACS_VLINE)
            self.content_win.addch(form_y + i, form_x + form_width - 1, curses.ACS_VLINE)
        
        # Draw corners
        self.content_win.addch(form_y, form_x, curses.ACS_ULCORNER)
        self.content_win.addch(form_y, form_x + form_width - 1, curses.ACS_URCORNER)
        self.content_win.addch(form_y + form_height, form_x, curses.ACS_LLCORNER)
        self.content_win.addch(form_y + form_height, form_x + form_width - 1, curses.ACS_LRCORNER)
        self.content_win.attroff(curses.color_pair(4))
        
        # Add form label
        self.content_win.addstr(form_y + 1, form_x + 2, prompt, curses.A_BOLD)
        
        # Add input field
        input_width = form_width - len(prompt) - 6
        win = curses.newwin(1, input_width, form_y + 1, form_x + len(prompt) + 3)
        win.bkgd(' ', curses.color_pair(7))  # White background for input field
        self.textbox = curses.textpad.Textbox(win)
        
        # Add instructions
        self.content_win.addstr(form_y + 3, form_x + 2, 
                          "Create a goal for any habit or behavior you want to track.", 
                          curses.color_pair(5))
        
        # Help text in footer
        self.footer_win.clear()
        self.footer_win.hline(0, 0, curses.ACS_HLINE, w)
        self.footer_win.addstr(1, (w - len(help_text)) // 2, help_text, curses.color_pair(2))
        
        # Refresh windows
        self.content_win.refresh()
        self.footer_win.refresh()
        win.refresh()  # Make sure the textbox window is drawn last


    def handle_create_goal(self):
        # Show cursor for text input
        curses.curs_set(1)
        self.stdscr.nodelay(False)
        
        # Get input from user
        text = self.textbox.edit()
        
        # Hide cursor again
        curses.curs_set(0)
        self.stdscr.nodelay(True)

        # Convert possible numeric escape characters to proper format
        goal_name = text.strip()
        
        # Check if text contains ESC character (ASCII 27 = \x1b)
        # and handle cancellation properly
        if '\x1b' in goal_name or not goal_name:
            self.set_status("Goal creation cancelled", error=False)
            self.current_state = 'menu'
        elif goal_name in self.goals:
            self.show_error(f"Goal '{goal_name}' already exists!")
        else:
            # Create new goal with current timestamp
            self.goals[goal_name] = {
                'counter': 0, 
                'history': [],
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.save_data()
            self.current_goal = goal_name
            self.current_state = 'view_goal'
            self.set_status(f"Goal '{goal_name}' created successfully!", error=False)


    # Deletion confirmation functions
    def draw_delete_confirm(self):
        h, w = self.content_win.getmaxyx()
        
        # Clear content area
        self.content_win.clear()
        
        # Create warning box
        box_width = 40
        box_height = 6
        box_x = (w - box_width) // 2
        box_y = (h - box_height) // 2
        
        # Draw warning box with red background
        for y in range(box_height):
            for x in range(box_width):
                if y == 0 or y == box_height - 1 or x == 0 or x == box_width - 1:
                    self.content_win.addch(box_y + y, box_x + x, ' ', curses.color_pair(3))
                else:
                    self.content_win.addch(box_y + y, box_x + x, ' ')
        
        # Warning icon and title
        self.content_win.addstr(box_y + 1, box_x + 2, "⚠ WARNING", curses.color_pair(3) | curses.A_BOLD)
        
        # Delete confirmation message
        msg = f"Delete goal '{self.goal_to_delete}'?"
        self.content_win.addstr(box_y + 3, box_x + (box_width - len(msg)) // 2, msg)
        
        # Options
        options = "[Y]es    [N]o"
        self.content_win.addstr(box_y + 5, box_x + (box_width - len(options)) // 2, options, curses.A_BOLD)
        
        # Help text in footer
        help_text = "Press Y to confirm deletion or N to cancel"
        self.footer_win.clear()
        self.footer_win.hline(0, 0, curses.ACS_HLINE, w)
        self.footer_win.addstr(1, (w - len(help_text)) // 2, help_text, curses.color_pair(2))
        
        # Refresh windows
        self.content_win.refresh()
        self.footer_win.refresh()

    def handle_delete_confirm(self):
        key = self.stdscr.getch()
        if key in [ord('y'), ord('Y')]:
            # Delete the goal
            deleted_name = self.goal_to_delete
            del self.goals[self.goal_to_delete]
            self.save_data()
            self.selected_index = max(0, min(self.selected_index, len(self.goals)-1))
            self.set_status(f"Goal '{deleted_name}' deleted successfully", error=False)
        elif key in [ord('n'), ord('N')]:
            self.set_status("Deletion cancelled", error=False)
        self.current_state = 'menu'

    # Status and notification methods
    def set_status(self, message, error=False):
        """Set a temporary status message that clears after a few seconds"""
        self.status_message = message
        self.status_time = time.time()
        self.is_error = error
        self.draw_status()
    
    def draw_status(self):
        """Draw the current status message in the footer"""
        h, w = self.stdscr.getmaxyx()
        self.footer_win.move(1, 0)
        self.footer_win.clrtoeol()
        
        if self.status_message:
            color = curses.color_pair(3) if self.is_error else curses.color_pair(4)
            self.footer_win.addstr(1, 1, self.status_message, color)
        self.footer_win.refresh()
    
    def show_error(self, message):
        """Show an error message and wait for input"""
        self.set_status(message, error=True)
        self.stdscr.getch()

    def quit(self):
        self.save_data()
        raise KeyboardInterrupt

def parse_args():
    parser = argparse.ArgumentParser(description='Impulse Check - Track your impulses and build better habits')
    parser.add_argument('--version', action='store_true', help='Show version and exit')
    return parser.parse_args()

def main(stdscr=None):
    if stdscr is None:
        curses.wrapper(run_app)
    else:
        run_app(stdscr)

def run_app(stdscr):
    ImpulseControlApp(stdscr)

def cli():
    args = parse_args()
    
    if args.version:
        print("ImpulseCheck v1.1.0")
        sys.exit(0)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n Commitment is staying true to your future self. Keep going!")

if __name__ == "__main__":
    cli()
