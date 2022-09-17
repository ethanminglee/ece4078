from os import stat
import pygame
import json
import re
import numpy as np
import math


class Game:
    '''
    Class for waypoint GUI and planning
    '''

    class Node:
        '''
        Node for RRT
        '''

        def __init__(self, x, y):
            self.x = x
            self.y = y
            self.path_x = []
            self.path_y = []
            self.parent = None


    class Fruit:
        '''
        Class for fruit markers
        '''
        ...


    class Marker:
        '''
        Class for Aruco markers
        '''

    


    def __init__(self, args):
        self.markers = None
        self.width, self.height = 600, 600
        self.waypoints = []
        self.map_file = args.map

        self.marker_locs = []
        self.fruit_locs = []

        if args.arena == 0:
            # sim dimensions
            self.arena_width = 3
        elif args.arena == 1:
            # real dimensions
            self.arena_width = 2

        self.scale_factor = self.width / self.arena_width
        # marker size is 70x70mm
        self.marker_size = 0.07

        pygame.init()
    
        self.font = pygame.font.SysFont('Arial', 25)
        self.canvas = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Waypoints')
        self.canvas.fill((255, 255, 255))

        # draw grid and add botty
        self.draw_grid()
        self.pi_bot = pygame.image.load('pics/8bit/pibot_top.png')
        self.canvas.blit(self.pi_bot, (self.width/2 - self.pi_bot.get_width()/2, self.height/2 - self.pi_bot.get_height()/2))
        pygame.display.update()

        # import images for aruco markers
        self.imgs = {"aruco1_0": pygame.image.load('pics/8bit/lm_1.png'),
                     "aruco2_0": pygame.image.load('pics/8bit/lm_2.png'),
                     "aruco3_0": pygame.image.load('pics/8bit/lm_3.png'),
                     "aruco4_0": pygame.image.load('pics/8bit/lm_4.png'),
                     "aruco5_0": pygame.image.load('pics/8bit/lm_5.png'),
                     "aruco6_0": pygame.image.load('pics/8bit/lm_6.png'),
                     "aruco7_0": pygame.image.load('pics/8bit/lm_7.png'),
                     "aruco8_0": pygame.image.load('pics/8bit/lm_8.png'),
                     "aruco9_0": pygame.image.load('pics/8bit/lm_9.png'),
                     "aruco10_0": pygame.image.load('pics/8bit/lm_10.png'),}

    
    def load(self):
        '''
        Load in map file
        '''
        with open(self.map_file, 'r') as f:
            markers = json.load(f)

        self.markers = markers
        self.draw_markers()
        print(self.fruit_locs)
        print(self.marker_locs)


    def draw_grid(self):
        '''
        Draw grid for ease of viewing
        '''
        blockSize = int(self.scale_factor / 10)

        for x in range(0, self.width, blockSize):
            for y in range(0, self.height, blockSize):
                rect = pygame.Rect(x, y, blockSize, blockSize)
                pygame.draw.rect(self.canvas, (122,122,122), rect, 1)


    def draw_coords(self, x, y, img = None, fruit = None):
        '''
        Draw markers on the screen given coordinates
        '''
        origin_x, origin_y = self.width/2, self.height/2
        conv_x = origin_x - x * self.width/2 / (self.arena_width / 2)
        conv_y = origin_y + y * self.height/2 / (self.arena_width / 2)

        if img:
            scale_size = self.marker_size * self.scale_factor
            img_scaled = pygame.transform.scale(img, (scale_size, scale_size))
            self.canvas.blit(img_scaled, (conv_x - scale_size/2, conv_y - scale_size/2))

            self.marker_locs.append((conv_x - scale_size/2, conv_y - scale_size/2))
        else:
            if fruit == 'apple':
                pygame.draw.circle(self.canvas, (255,0,0), (conv_x, conv_y), 5)
                pygame.draw.circle(self.canvas, (255,0,0), (conv_x, conv_y), 5 * (self.scale_factor / 10), 1)
            elif fruit == 'lemon':
                pygame.draw.circle(self.canvas, (255,255,0), (conv_x, conv_y), 5)
                pygame.draw.circle(self.canvas, (255,255,0), (conv_x, conv_y), 5 * (self.scale_factor / 10), 1)
            elif fruit == 'orange':
                pygame.draw.circle(self.canvas, (255,102,0), (conv_x, conv_y), 5)
                pygame.draw.circle(self.canvas, (255,102,0), (conv_x, conv_y), 5 * (self.scale_factor / 10), 1)
            elif fruit == 'pear':
                pygame.draw.circle(self.canvas, (0,255,0), (conv_x, conv_y), 5)
                pygame.draw.circle(self.canvas, (0,255,0), (conv_x, conv_y), 5 * (self.scale_factor / 10), 1)
            elif fruit == 'strawberry':
                pygame.draw.circle(self.canvas, (255,0,255), (conv_x, conv_y), 5)
                pygame.draw.circle(self.canvas, (255,0,255), (conv_x, conv_y), 5 * (self.scale_factor / 10), 1)

            self.fruit_locs.append((conv_x, conv_y))

        pygame.display.update()


    def draw_markers(self):
        '''
        Draw all markers and fruit from the map file
        '''
        for key in self.markers:
            try:
                self.draw_coords(self.markers[key]['x'], self.markers[key]['y'], img=self.imgs[key])
            except:
                self.draw_coords(self.markers[key]['x'], self.markers[key]['y'], fruit=re.sub(r'[^a-zA-Z]', '', key))


    def draw_waypoints(self):
        '''
        Draw waypoints
        '''
        for waypoint in self.waypoints:
            pygame.draw.rect(self.canvas, (235,161,52), pygame.Rect(waypoint.left, waypoint.top, 10, 10))


    def add_text(self):
        '''
        Add text to the waypoints to see the order in which the bot will visit the waypoints
        '''
        i = 1
        for waypoint in self.waypoints:
            self.canvas.blit(self.font.render(f'{i}', True, (0,0,0)), (waypoint.left, waypoint.top))
            i += 1


    def convert_to_world(self, pos):
        '''
        Convert from the GUI points to points in the world frame
        '''
        origin_x, origin_y = self.width/2, self.height/2
        x, y = pos
        world_x = (origin_x - x) / (self.width/2 / (self.arena_width / 2))
        world_y = (y - origin_y) / (self.height/2 / (self.arena_width / 2))

        return world_x, world_y


    def is_over(self, mouse_pos):
        '''
        Check if the mouse click has occurred over an existing marker
        '''
        for waypoint in self.waypoints:
            if waypoint.collidepoint(mouse_pos):
                return waypoint
        return None


    def place_waypoint(self, mouse_pos):
        '''
        Place a waypoint on the screen
        '''
        waypoint = pygame.draw.rect(self.canvas, (235,161,52), pygame.Rect(mouse_pos[0]-5, mouse_pos[1]-5, 10, 10) )
        self.waypoints.append(waypoint)
        self.add_text()


    def remove_waypoint(self, waypoint):
        '''
        Remove a waypoint if one has been clicked 
        '''
        self.waypoints.remove(waypoint)

        # reset canvas and redraw points
        self.canvas.fill((255,255,255))
        self.draw_grid()
        self.draw_markers()
        self.draw_waypoints()
        self.add_text()
        self.canvas.blit(self.pi_bot, (self.width/2 - self.pi_bot.get_width()/2, self.height/2 - self.pi_bot.get_height()/2))


    def write_waypoints(self):
        '''
        Write waypoints to a file (testing purposes)
        '''
        with open('waypoints.txt', 'w+') as f:
            for waypoint in self.waypoints:
                x, y = self.convert_to_world(waypoint.center)
                f.write(f'{x} {y}\n')


    def run(self):
        '''
        Run the GUI
        '''

        self.load()
        running = True
        while running:
            pygame.display.update()

            for event in pygame.event.get():
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        mouse_presses = pygame.mouse.get_pressed()

                        if mouse_presses[0]:
                            mouse_pos = pygame.mouse.get_pos()
                            waypoint = self.is_over(mouse_pos)
                            if waypoint is None:
                                self.place_waypoint(mouse_pos)
                            else:
                                self.remove_waypoint(waypoint)
                            self.write_waypoints()
                    elif event.type == pygame.QUIT:
                        running = False

    '''
    Functions for RRT planning from now on
    '''

    def rrt(self, start = np.zeros(2),
                 goal = np.array([0,0]),
                 expand_dis = 3.0,
                 path_resolution = 0.5,
                 max_points = 200):
        '''
        Function for RRT planning
        '''
        start_pos = self.Node(start[0], start[1])
        end_pos = self.Node(goal[0], goal[1])

        node_list = [start_pos]
        
        while len(node_list) <= max_points:
            ...
        return


    def is_in_collision_with_points(self, points):

        points_in_collision = []


    def is_collision_free(self, new_node):
        ...

    
    def get_random_node(self):
        x = self.width * np.random.random_sample()
        y = self.height * np.random.random_sample()
        return self.Node(x, y)


    @staticmethod
    def get_nearest_node_index(node_list, rnd_node):

        dlist = [(node.x - rnd_node.x) ** 2 + (node.y - rnd_node.y)
                ** 2 for node in node_list]
        return np.argmin(dlist)


    @staticmethod
    def calc_distance_and_angle(from_node, to_node):
        dx = to_node.x - from_node.x
        dy = to_node.y - from_node.y
        d = math.hypot(dx, dy)
        theta = math.atan2(dy, dx)
        return d, theta



if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--arena", metavar='', type=int, default=0)
    parser.add_argument("--map", metavar='', type=str, default='M4_true_map.txt')
    args, _ = parser.parse_known_args()

    game = Game(args)
    game.run()
    

