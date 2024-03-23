# A mishmosh of a discord bot. for fun!
# pls do not read this code, it is uggo

import discord
from pyfiglet import Figlet
import re
import argparse
from nba_api.live.nba.endpoints import scoreboard

# -test to do a local repl
parser = argparse.ArgumentParser()
parser.add_argument('-test', action='store_true')
args = parser.parse_args()

# set up the discord client
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
  print(f'We have logged in as {client.user}')


@client.event
async def on_message(message):
  if message.author == client.user:
    return

  print(f'Received message: {message.content}')
  response = response_for_text(message.content)
  if response:
    print(f'Will respond: {response}')
    await message.channel.send(response)
  else:
    print('No response')


def response_for_text(text):
  parts = text.split(' ')
  if text.startswith('$hello'):
      return 'Hello!'
  elif text.startswith('$big'):
    if len(parts) > 1:
      text = parts[1]
      return '```' + make_big_text(text) + '```'
  elif text.startswith('$help'):
    return make_help_text()
  elif text.startswith('$echo'):
    if len(parts) > 1:
      return ' '.join(parts[1:])
  elif text.startswith('$lakers'):
    return make_lakers_text()


def make_big_text(text):
  font = Figlet(font='doh')
  return font.renderText(text)  


def make_help_text():
  return '''Here are some things you can try!

  $hello
  $big <text>
  $echo <text>
  $lakers

  Check back soon for more features!
  '''


def make_lakers_text():
  games = scoreboard.ScoreBoard().get_dict()['scoreboard']['games']
  for game in games:
    home_team = game['homeTeam']['teamName']
    away_team = game['awayTeam']['teamName']
    if home_team != 'Lakers' and away_team != 'Lakers':
      continue
    lakers_home = home_team == 'Lakers'
    home_score = game['homeTeam']['score']
    away_score = game['awayTeam']['score']
    lakers_score = home_score if lakers_home else other_score
    other_score = away_score if lakers_home else home_score
    other_team = away_team if lakers_home else home_team
    game_status_text = game['gameStatusText']
    if game['gameStatus'] == 1:
      return f'Lakers are playing tonight at {game_status_text}!'
    elif game['gameStatus'] == 3:
      if lakers_score > other_score:
        return f'The Lakers won tonight! They beat the {other_team} {lakers_score}-{other_score}.'
      else:
        return f'Dang, the Lakers fell short tonight. They lost to the {other_team} {other_score}-{lakers_score}.'
    else:
      text = f'The game\'s on now! '
      if game_status_text == 'Half':
        text += 'It\'s halftime. '
      else:
        period = game['period']
        time_text = game_status_text[3:]
        text += f'We\'re in the {period}{get_suffix(period)} quarter with {time_text} left. '
      if lakers_score > other_score:
        text += f'Lakers are up {lakers_score - other_score} on the {other_team}! {lakers_score}-{other_score}. Let\'s go!!!'
      elif lakers_score < other_score:
        text += f'Lakers are trailing by {lakers_score - other_score} to the {other_team}. It\'s {lakers_score}-{other_score}. We got this.'
      else:
        text += f'It\'s all tied up at {lakers_score}! Let\'s beat the {other_team}!'
      return text
  return 'The Lakers aren\'t playing tonight. Go outside.'


def get_suffix(num):
  if num == 1:
    return 'st'
  elif num == 2:
    return 'nd'
  else:
    return 'th'


# do the thing
if args.test:
  while True:
    prompt = input()
    response = response_for_text(prompt)
    if response:
      print(response)
else:
  token_file = open("token.txt", "r")
  client.run(token_file.read())
  token_file.close()


