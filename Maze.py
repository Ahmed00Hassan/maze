import tkinter as tk
from tkinter import filedialog, messagebox
import threading

import sys

class Node():

    """node class represents each position in maze with pathfinding  inforamtion"""
    
    def __init__(self, state, parent, action):
        #basic node info
        self.state = state     # (row, col) position in maze
        self.parent = parent   # parent node for path reconstruction
        self.action = action   # movement direction that led to this node


#BFS algrothms
class QueueFrontier():
    """ frontier for bfs using fifo (first in first out) priciiple """

    def __init__(self):
        self.frontier = []

    def add(self, node):
        """add node to end of frontier"""
        self.frontier.append(node)

    def contains_state(self, state):
        """check if frontier contains specfic state"""
        return any(node.state == state for node in self.frontier)

    def empty(self):
        """check if frontier is empty"""
        return len(self.frontier) == 0

    ##remove beginning of the list
    def remove(self):
        if self.empty():
            raise Exception('empty frontier')
        else:
            node =self.frontier[0]
            self.frontier = self.frontier[1:]
            return node
        

class Maze():
    """main maze class handling both BFS"""
    def __init__(self, filename):
        with open(filename) as f:
            contents = f.read()


        #validate maze format
        if contents.count("A") != 1:
            raise Exception("Maze must have exactly one start point")
        if contents.count("B") != 1:
            raise Exception("Maze must have exactly one goal")

        # parse maze layout
        contents = contents.splitlines()
        self.height = len(contents)
        self.width = max(len(line) for line in contents)
        self.walls = []


        # create wall matrix and find start/goal positions
        for i in range(self.height):
            row = []
            for j in range(self.width):
                try:
                    if contents[i][j] == "A":
                        self.start = (i, j)
                        row.append(False)
                    elif contents[i][j] == "B":
                        self.goal = (i, j)
                        row.append(False)
                    elif contents[i][j] == " ":
                        row.append(False)
                    else:
                        row.append(True)
                except IndexError:
                    row.append(False)
            self.walls.append(row)

        self.solution = None

    def print(self):
        """visualize maze with solution path"""
        solution = self.solution[1] if self.solution is not None else None
        print()
        for i, row in enumerate(self.walls):
            for j, col in enumerate(row):
                if col:
                    print("#", end="")
                elif (i, j) == self.start:
                    print("A", end="")
                elif (i, j) == self.goal:
                    print("B", end="")
                elif solution is not None and (i, j) in solution:
                    print("*", end="")
                else:
                    print(" ", end="")
            print()
        print()

    def neighbors(self, state):
        """find vaild neighboring cells"""
        row, col = state
        candidates = [
            ("up", (row - 1, col)),
            ("down", (row + 1, col)),
            ("left", (row, col - 1)),
            ("right", (row, col + 1))
        ]
        result = []
        #check if neighbor is within bounds and not a wall
        for action, (r, c) in candidates:
            if 0 <= r < self.height and 0 <= c < self.width:
                if not self.walls[r][c]:
                    result.append((action, (r, c)))
        return result
    
    def heuristic(state, goal):
        """calculate heuristic for A*"""
        row1, col1 = state
        row2, col2 = goal
        return abs(row1 - row2) + abs(col1 - col2)

    def solve(self):
        """Finds a solution to maze if one exists"""

        #keep track of number of state explored
        self.num_explored =0

        #Initialize frontier to just the starting positon
        start =Node(state =self.start, parent=None, action=None)
        frontier = QueueFrontier()
        frontier.add(start)

        #Initialize on empty explored set
        self.explored = set()

        #keep looping until solution found
        while True:

            #if nothing left in frontier then no path
            if frontier.empty():
                raise Exception('no solution')

            #choose a node from the frontier
            node = frontier.remove()
            self.num_explored += 1

            #if node is the goal then we have a solution
            if node.state == self.goal:
                actions =[]
                cells =[]
                #follow parent nodes to find solution
                while node.parent is not None:
                    actions.append(node.action)
                    cells.append(node.state)
                    node = node.parent
                actions.reverse()
                cells.reverse()
                self.solution = (actions,cells)
                return

            #Mark node as explored
            self.explored.add(node.state)

            #Add neighbors to frontier
            for action, state in self.neighbors(node.state):
                if not frontier.contains_state(state) and state not in self.explored:
                    child = Node(state =state, parent=node,action=action)
                    frontier.add(child)

class MazeApp:
    def __init__(self, root):
        # Initialize main window
        self.root = root
        self.root.title("Robot path planning (BFS)")
        self.root.geometry("800x600")  # Set window dimensions to 800x600 pixels
        
        # Color configuration for different maze elements
        self.colors = {
            'wall': '#2c3e50',    # Dark blue-grey for walls
            'path': '#ecf0f1',    # Off-white for paths
            'start': '#2ecc71',   # Green for start point
            'goal': '#e74c3c',    # Red for goal point
            'solution': '#3498db' # Blue for solution path
        }
        
        # Maze display settings
        self.cell_size = 45       # Size of each cell in pixels
        self.animation_delay = 0.4  # Delay between animation steps (seconds)
        self.is_animating = False # Flag to track animation state

        # Create control panel for buttons
        control_frame = tk.Frame(root)
        control_frame.pack(pady=5)

        # Load Maze button
        self.btn_load = tk.Button(control_frame, 
                                text="Load Maze", 
                                command=self.load_maze)
        self.btn_load.pack(side=tk.LEFT, padx=5)

        # Solve button (initially disabled)
        self.btn_solve = tk.Button(control_frame, 
                                 text="Solve", 
                                 command=self.solve_maze, 
                                 state=tk.DISABLED)
        self.btn_solve.pack(side=tk.LEFT, padx=5)

        # Create scrollable canvas for maze display
        self.canvas = tk.Canvas(root, bg='white')
        self.scroll_x = tk.Scrollbar(root, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.scroll_y = tk.Scrollbar(root, orient=tk.VERTICAL, command=self.canvas.yview)
        
        # Configure canvas scrolling
        self.canvas.configure(xscrollcommand=self.scroll_x.set, 
                            yscrollcommand=self.scroll_y.set)

        # Position UI elements
        self.scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.maze = None  # Will store maze object

    def load_maze(self):
        """Handle maze file selection and loading"""
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if path:
            try:
                # Initialize maze and draw it
                self.maze = Maze(path)
                self.draw_maze()
                self.btn_solve.config(state=tk.NORMAL)
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def draw_maze(self):
        """Render maze on canvas with colored cells"""
        self.canvas.delete("all")  # Clear previous maze
        rows = self.maze.height
        cols = self.maze.width
        
        # Set canvas scroll area based on maze size
        canvas_width = cols * self.cell_size
        canvas_height = rows * self.cell_size
        self.canvas.config(scrollregion=(0, 0, canvas_width, canvas_height))

        # Draw each cell in the maze
        for i in range(rows):
            for j in range(cols):
                # Calculate cell coordinates
                x1 = j * self.cell_size
                y1 = i * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                # Determine cell color based on type
                if self.maze.walls[i][j]:
                    color = self.colors['wall']
                elif (i, j) == self.maze.start:
                    color = self.colors['start']
                elif (i, j) == self.maze.goal:
                    color = self.colors['goal']
                else:
                    color = self.colors['path']

                # Draw cell rectangle with border
                self.canvas.create_rectangle(x1, y1, x2, y2, 
                                           fill=color, 
                                           outline='#bdc3c7')  # Light grey border
                
                # Add labels for start and goal positions
                if (i, j) == self.maze.start:
                    self.canvas.create_text(x1 + self.cell_size//2, 
                                          y1 + self.cell_size//2,
                                          text="A", 
                                          font=('Arial', 12, 'bold'))
                elif (i, j) == self.maze.goal:
                    self.canvas.create_text(x1 + self.cell_size//2, 
                                          y1 + self.cell_size//2,
                                          text="B", 
                                          font=('Arial', 12, 'bold'))

    def solve_maze(self):
        """Initiate maze solving process in background thread"""
        def solve_thread():
            try:
                # Disable solve button during operation
                self.btn_solve.config(state=tk.DISABLED)
                self.is_animating = True
                
                # Solve the maze using BFS
                self.maze.solve()
                
                # Start animation in main thread
                self.root.after(0, self.animate_solution, 0)
            except Exception as e:
                # Show error message if solving fails
                self.root.after(0, messagebox.showerror, "Error", str(e))
                self.is_animating = False
                self.btn_solve.config(state=tk.NORMAL)

        # Start solving thread if not already running
        if not self.is_animating:
            threading.Thread(target=solve_thread, daemon=True).start()

    def animate_solution(self, step):
        """Animate solution path step-by-step"""
        if step < len(self.maze.solution[1]):
            # Get current position in solution path
            i, j = self.maze.solution[1][step]
            
            # Skip animating start/goal positions
            if (i, j) not in (self.maze.start, self.maze.goal):
                # Calculate cell coordinates
                x1 = j * self.cell_size
                y1 = i * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                
                # Draw solution path segment
                self.canvas.create_rectangle(x1, y1, x2, y2,
                                           fill=self.colors['solution'],
                                           outline='#bdc3c7',
                                           tags=('solution', f'sol_{i}_{j}'))
            
            # Schedule next animation step
            self.root.after(int(self.animation_delay * 1000), 
                          self.animate_solution, step + 1)
        else:
            # Finalize animation
            self.is_animating = False
            self.btn_solve.config(state=tk.NORMAL)
            messagebox.showinfo("Success", "Solution found!")

if __name__ == "__main__":
    # Initialize and run the application
    root = tk.Tk()
    app = MazeApp(root)
    root.mainloop()