import kivy
kivy.require('1.8.0')

from random import randint

from kivy.app import App
from kivy.config import Config
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.uix.scatter import Scatter
from kivy.animation import Animation
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty
from kivy.graphics import Color, Rectangle

from tetrominoes import tetros
from game import *

# Set window to same resolution as Nexus 4
Config.set('graphics','width','1280')
Config.set('graphics','height','768')

grid_size_x = 20
grid_size_y = 20

sprite_size = 32

# Shows a single lonesome tetromino
class TetroGrid(GridLayout):
	def setup(self, tetromino, fungus, ftype='norm'):
		self.clear_widgets()
		self.col_default_width = sprite_size
		self.row_default_height = sprite_size
		self.rows = len(tetromino)
		self.cols = len(tetromino[0])
		self.size = ( sprite_size*self.cols, sprite_size*self.rows )
		# Add each block to the GridLayout
		for y in range(self.rows):
			for x in range(self.cols):
				b = GridBlock()
				b.background = False
				b.ftype = ftype
				if tetromino[y][x]:
					b.fungus = 'Green'

					# Join neighboring blocks
					neighbors = ''
					# Up
					if y > 0:
						if tetromino[y-1][x]:
							neighbors = neighbors+'u'
					# Left
					if x > 0:
						if tetromino[y][x-1]:
							neighbors = neighbors+'l'
					# Right
					if x < self.cols-1:
						if tetromino[y][x+1]:
							neighbors = neighbors+'r'
					# Down
					if y < self.rows-1:
						if tetromino[y+1][x]:
							neighbors = neighbors+'d'
					b.neighbors = neighbors

				self.add_widget(b)


# A single grid block containing either a fungus or nothing
class GridBlock(FloatLayout):
	fungus = StringProperty('None')
	ftype = StringProperty('norm')
	neighbors = StringProperty('')
	background = BooleanProperty(True)
	sprite = ObjectProperty(None)
	grid_background = ObjectProperty(None)

	def on_fungus(self, instance, value):
		self.update_sprite()
	def on_ftype(self, instance, value):
		self.update_sprite()
	def on_neighbors(self, instance, value):
		self.update_sprite()
	def on_background(self, instance, value):
		if value:
			self.grid_background.source = 'Grid/block.png'
		else:
			self.grid_background.source = 'blank.png'
	def update_sprite(self):
		if self.fungus == 'None':
			self.sprite.source = 'blank.png'
		else:
			if self.neighbors == '':
				self.sprite.source = 'atlas://'+self.fungus+'/'+self.ftype+'/x'
			else:
				self.sprite.source = 'atlas://'+self.fungus+'/'+self.ftype+'/'+self.neighbors

# Drag and zoomable view of the entire game grid
class GameGridView(Scatter):
	gglayout = GridLayout(cols = grid_size_x,
			      rows = grid_size_y,
			      col_default_width = sprite_size,
			      row_default_height = sprite_size,
			      padding=0,
			      pos_hint=(None,None),
			      size=( sprite_size*grid_size_x, sprite_size*grid_size_y ))

	def __init__(self, **kwargs):
		super(GameGridView, self).__init__(**kwargs)
		self.size = self.gglayout.size
		self.gglayout.pos = self.pos
		self.add_widget(self.gglayout)

	def setup(self, grid):
		self.gglayout.clear_widgets()
		for y in grid:
			for x in y:
				self.gglayout.add_widget(x)

	def on_touch_down(self, touch):
		if self.parent.collide_point(*touch.pos):
			super(GameGridView, self).on_touch_down(touch)
		if touch.is_double_tap:
			self.center = self.parent.center
			self.scale = 1
		if touch.is_mouse_scrolling:
			if touch.button == 'scrollup':
				self.scale -= 0.1
			else:
				self.scale += 0.1
	
	def on_touch_move(self, touch):
		if self.parent.collide_point(*touch.pos):
			super(GameGridView, self).on_touch_move(touch)

	def global_coords_to_block(self, x, y):
		x, y = self.to_local(x, y)
		x = int( x / sprite_size )
		y = int( (self.gglayout.height-y) / sprite_size )
		return x, y

# Layout dividers
class VertLine(Widget):
	pass
class HorizLine(Widget):
	pass

# Outline showing where new blocks will be placed
class Ghost(Scatter):
	ghost_grid = ObjectProperty(None)

	def setup(self, np, color):
		self.ghost_grid.setup( np, color, 'ghost' )
		self.ghost_grid.y = sprite_size - self.ghost_grid.height
			
	def on_touch_up(self, touch):
		super(Ghost, self).on_touch_up(touch)
		x, y = self.parent.ggview.global_coords_to_block( *touch.pos )
		self.parent.place_block( x, y )
		self.parent.remove_widget(self)

	def on_touch_move(self, touch):
		# Snap when inside grid
		g_x, g_y = self.parent.ggview.to_local(*touch.pos)
		s_x, s_y = self.parent.ggview.gglayout.size
		scale = self.parent.ggview.scale
		if g_x > 0 and g_x < s_x and g_y > 0 and g_y < s_y:
			self.x = int(g_x/sprite_size)*sprite_size*scale + self.parent.ggview.x
			self.y = int(g_y/sprite_size)*sprite_size*scale + self.parent.ggview.y
		else:
			self.center = touch.pos 

class NewPieceBox(Widget):
	pass

class PlayerWidget(Widget):
	new_piece_box = ObjectProperty(None)
	name_label = ObjectProperty(None)

class FungusGame(FloatLayout):
	side_panel = ObjectProperty(None)
	ggview = ObjectProperty(None)
	ghost = None
	grid = []
	players = []
	curr_player_num = 0
	new_piece = tetros[0]

	def new_game(self):
		# Setup players
		self.players = [ Player(  'Green', 'Algae' ),
				 Player(    'Red', 'Penicillium' ),
				 Player(   'Blue', 'Nanites'),
				 Player( 'Yellow', 'E Coli') ]
		# Initialize player widgets and add them to the side panel
		for n in range(len(self.players)):
			p = self.players[n]
			p.panel = PlayerWidget()
			p.panel.name_label.text = p.name
			p.panel.remove_widget( p.panel.new_piece_box )		# This is dumb, but otherwise it doesn't have the right position
			self.side_panel.add_widget( p.panel )
			# Add dividers
			if n < len(self.players)-1:
				self.side_panel.add_widget( HorizLine() )
		self.curr_player_num = randint( 0, len(self.players)-1 )
		# Choose random starting player
		self.curr_player = self.players[ self.curr_player_num ]
		self.curr_player.panel.add_widget( self.curr_player.panel.new_piece_box )
		# Initialize matrix of block objects.
		# Because of the way GridLayout fills itself, coordinates are [Y][X]
		# from top left corner.
		self.grid = []
		for y in range(grid_size_y):
			self.grid.append([])
			for x in range(grid_size_x):
				self.grid[y].append(GridBlock())

		# Add home blocks
		self.grid[5][5].fungus = 'Green'
		self.grid[5][5].ftype = 'home'
		self.grid[5][grid_size_x-6].fungus = 'Red'
		self.grid[5][grid_size_x-6].ftype = 'home'
		self.grid[grid_size_y-6][grid_size_x-6].fungus = 'Blue'
		self.grid[grid_size_y-6][grid_size_x-6].ftype = 'home'
		self.grid[grid_size_y-6][5].fungus = 'Yellow'
		self.grid[grid_size_y-6][5].ftype = 'home'

		self.ggview.setup(self.grid)

		# Choose random starting piece
		self.new_piece = tetros[ randint(0,9) ]
		self.curr_player.panel.new_piece_grid.setup( self.new_piece, self.players[0].color )
	
	def on_touch_down(self, touch):
		super(FungusGame, self).on_touch_down(touch)
		# If player is trying to drag the new piece, generate ghost
		new_piece_box = self.curr_player.panel.new_piece_box
		if new_piece_box.collide_point(*touch.pos):
			self.ghost = Ghost()
			self.ghost.center = new_piece_box.center
			self.ghost.scale = self.ggview.scale
			self.ghost.setup( self.new_piece, self.curr_player.color )
			self.add_widget(self.ghost)
	
	def on_touch_up(self, touch):
		super(FungusGame, self).on_touch_up(touch)
		# If player taps the box, rotate new piece
		new_piece_box = self.curr_player.panel.new_piece_box
		if new_piece_box.collide_point(*touch.pos):
			self.new_piece.rotate()
			self.curr_player.panel.new_piece_grid.setup( self.new_piece, self.curr_player.color )
			self.curr_player.panel.new_piece_grid.center = self.curr_player.panel.center

	def place_block(self, x, y):
		t_height = len(self.new_piece)
		t_width = len(self.new_piece[0])
		# Check boundries
		if (y<0) or (x<0):
			return 1
		if ( y+t_height > grid_size_y ) or ( x+t_width > grid_size_x ):
			return 1
		# Check for Collisions
		for ty in range(t_height):
			for tx in range(t_width):
				if self.new_piece[ty][tx]:
					if self.grid[y+ty][x+tx].fungus != 'None':
						# Stop here and do not place piece
						# Might be better to raise an exception
						return 1
		# Copy new piece onto game grid
		for ty in range(len(self.new_piece)):
			for tx in range(len(self.new_piece[ty])):
				if self.new_piece[ty][tx]:
					self.grid[y+ty][x+tx].fungus = self.curr_player.color
		self.update_neighbors(self.grid)
	
	def update_neighbors(self, grid):
		y_len = len(grid)
		x_len = len(grid[0])
		for y in range(y_len):
			for x in range(x_len):
				fungus = grid[y][x].fungus
				if fungus != 'None':
					neighbors = ''
					# Up
					if y > 0:
						if grid[y-1][x].fungus == fungus:
							neighbors = neighbors+'u'
					# Left
					if x > 0:
						if grid[y][x-1].fungus == fungus:
							neighbors = neighbors+'l'
					# Right
					if x < x_len-1:
						if grid[y][x+1].fungus == fungus:
							neighbors = neighbors+'r'
					# Down
					if y < y_len-1:
						if grid[y+1][x].fungus == fungus:
							neighbors = neighbors+'d'
					grid[y][x].neighbors = neighbors

class FungusApp(App):
	def build(self):
		self.icon = 'icon.png'
		game = FungusGame()
		game.new_game()
		return game

if __name__ == '__main__':
	FungusApp().run()
