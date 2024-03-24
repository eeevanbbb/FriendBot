# A mishmosh of a discord bot. for fun!
# pls do not read this code, it is uggo

import discord
from pyfiglet import Figlet
import re
import argparse
from nba_api.live.nba.endpoints import scoreboard
import gensim
import random
import google.generativeai as genai
import python_weather
import asyncio

# -test to do a local repl
parser = argparse.ArgumentParser()
parser.add_argument('-test', action='store_true')
args = parser.parse_args()

# set up the discord client
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# global setup
# limit model to 100k so GCP micro instance doesn't explode
word_model = gensim.models.KeyedVectors.load_word2vec_format('GoogleNews-vectors-negative300.bin', binary=True, limit=100000)

# set up gemini
gemini_token_file = open("gemini_token.txt", "r")
gemini_api_key = gemini_token_file.read()
gemini_token_file.close()
genai.configure(api_key=gemini_api_key.rstrip())
gemini_model = genai.GenerativeModel('gemini-pro')


@client.event
async def on_ready():
  print(f'We have logged in as {client.user}')


@client.event
async def on_message(message):
  if message.author == client.user:
    return

  print(f'Received message: {message.content}')
  text_response = maybe_make_text_response(message.content)
  if text_response:
    print(f'Will respond: {text_response}')
    idx = 0
    MAX_LEN = 2000
    while len(text_response) > idx:
      chunk = text_response[idx:idx + MAX_LEN]
      await message.channel.send(chunk)
      idx += MAX_LEN
  else:
    print('No response')


def maybe_make_text_response(text):
  parts = text.split(' ')
  if text.startswith('$hello'):
      return 'Hello!'
  elif text.startswith('$big'):
    if len(parts) > 1:
      text = parts[1]
      return '```' + make_big_text(text) + '```'
    else:
      return 'What word do you want me to make big?'
  elif text.startswith('$help'):
    return make_help_text()
  elif text.startswith('$echo'):
    if len(parts) > 1:
      return ' '.join(parts[1:])
    else:
      return 'What do you want me to echo?'
  elif text.startswith('$lakers'):
    return make_lakers_text()
  elif text.startswith('$semantle'):
    if len(parts) > 1:
      word = parts[1]
      return make_similar_words(word)
    else:
      return 'What word do you want me to guess similar words for?'
  elif text.startswith('$who'):
    return make_who_text()
  elif text.startswith('$dice'):
    return make_dice_text()
  elif text.startswith('$rhyme'):
    if len(parts) > 1:
      word = parts[1]
      return make_rhymes_text(word)
    else:
      return 'What word would you like rhymes for?'
  elif text.startswith('$joke'):
    return make_joke_text()
  elif text.startswith('$poem'):
    if len(parts) > 1:
      topic = parts[1]
      return make_poem_text(topic)
    else:
      return 'On which topic would you like me to wax poetic?'
  elif text.startswith('$weather'):
    if len(parts) > 1:
      city = ' '.join(parts[1:])
      return make_weather_summary(city)
    else:
      return make_weather_summary('Los Angeles')
  elif text.startswith('$ '):
    if len(parts) > 1:
      return get_gemini_response(parts[1:])
    else:
      return 'Are you trying to talk to me? Try $help to see what I can do!'
  elif text.startswith('$'):
    return 'Sorry, I don\'t know that one yet.'


def make_big_text(text):
  font = Figlet(font='letters')
  return font.renderText(text)  


def make_rhymes_text(word):
  try:
    return gemini_model.generate_content(f'List up to 10 words that rhyme with {word}').text
  except:
    return f'Sorry, I can\'t rhyme with {word} 😬'


def make_joke_text():
  try:
    return gemini_model.generate_content('Tell me a joke').text
  except:
    return f'Sorry, I\'m not feeling funny today 😬'


def get_gemini_response(text):
  try:
    return gemini_model.generate_content(text).text
  except:
    return 'Sorry, I can\'t answer that 😬'


def make_poem_text(topic):
  try:
    return gemini_model.generate_content(f'Write me a poem about {topic}').text
  except:
    return 'Sorry, I can\'t write a poem about {topic} 😬'


def make_help_text():
  return '''Here are some things you can try!

  $big <word>
  $dice
  $echo <text>
  $hello
  $joke
  $lakers
  $poem <topic>
  $rhyme <word>
  $semantle <word>
  $weather <city>

  Check back soon for more features!'''


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
        text += f'Lakers are trailing by {other_score - lakers_score} to the {other_team}. It\'s {lakers_score}-{other_score}. We got this.'
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


def make_similar_words(word):
  text = ''
  for word, similarity in word_model.most_similar(positive=[word], topn=10):
    if '_' in word:
      continue
    text += f'- {word}\n'
  return text


def make_who_text():
  return '''It\'s me, FriendBot!

  I\'m here for funsies! Check out $help to see what I can do. If I break down, please pour one out for my creator who has to debug this nonsense.

  I\'m looking forward to being your friend!'''


def make_dice_text():
  rand1 = random.randint(1, 6)
  rand2 = random.randint(1, 6)
  return f'{num_to_emoji(rand1)} {num_to_emoji(rand2)}'


def num_to_emoji(num):
  if num == 1:
    return '1️⃣'
  elif num == 2:
    return '2️⃣'
  elif num == 3:
    return '3️⃣'
  elif num == 4:
    return '4️⃣'
  elif num == 5:
    return '5️⃣'
  elif num == 6:
    return '6️⃣'  
  return f'{num}'


def make_weather_summary(city):
  raw_weather = ''
  if args.test:
    raw_weather = asyncio.run(fetch_weather_data(city))
  else:
    raw_weather = await fetch_weather_data(city)
  try:
    return gemini_model.generate_content(f'Summarize this weather data including the city and use emojis: {raw_weather}').text
  except:
    return f'I was unable to get the weather for {city} 😬'


async def fetch_weather_data(city):
  data = []
  async with python_weather.Client(unit=python_weather.IMPERIAL) as client:
    weather = await client.get(city)  
    data.append(weather.location)  
    for daily in weather.daily_forecasts:
      data.append(str(daily))      
      for hourly in daily.hourly_forecasts:
        data.append(f' --> {hourly!r}')        
  return '\n'.join(data)


# do the thing
if args.test:
  while True:
    prompt = input()
    response = maybe_make_text_response(prompt)
    if response:
      print(response)
else:
  token_file = open("token.txt", "r")
  client.run(token_file.read())
  token_file.close()
