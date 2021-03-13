import re
from . import subs

re_pos = r"(\\pos\(([0-9]+|[0-9]+\.[0-9]+), *([0-9]+|[0-9]+\.[0-9]+)\))"
re_move = r"(\\move\(([0-9\-,\.]+)\))"
re_clip = r"(\\clip\((.+)\))"

re_draw = r"\{.*?\\p[1-9][0-9]*.*?\}([^\{]+)"

re_tag = r"\{.*?\}"

re_simple = [
  (r"(\\fs([0-9]+\.[0-9]+|[0-9]+))", "\\fs{}"),
  (r"(\\fsp([0-9]+\.[0-9]+|[0-9]+))", "\\fsp{}"),
  (r"(\\bord([0-9]+\.[0-9]+|[0-9]+))", "\\bord{}"),
  (r"(\\xbord([0-9]+\.[0-9]+|[0-9]+))", "\\xbord{}"),
  (r"(\\ybord([0-9]+\.[0-9]+|[0-9]+))", "\\ybord{}"),
  (r"(\\shad([0-9]+\.[0-9]+|[0-9]+))", "\\shad{}"),
  (r"(\\xshad([0-9]+\.[0-9]+|[0-9]+))", "\\xshad{}"),
  (r"(\\yshad([0-9]+\.[0-9]+|[0-9]+))", "\\yshad{}"),
  (r"(\\blur([0-9]+\.[0-9]+|[0-9]+))", "\\blur{}"),
  (r"(\\be([0-9]+\.[0-9]+|[0-9]+))", "\\be{}"),
]

num = lambda n: round(n, 3) if n % 1 else int(n)


def scale(src, scale_width, scale_height):
  events = src._find_section(subs.EVENTS_SECTION)
  for event in events.events:
    matches = re.findall(re_draw, event.text)
    for match in matches:
      numbers = []
      for number in match.split(" "):
        try:
          numbers.append(num(float(number) * scale_height))
        except:
          numbers.append(number)
      numbers = [str(number) for number in numbers]
      scaled = " ".join(numbers)
      event.text = event.text.replace(match, scaled)

    groups = re.findall(re_tag, event.text)
    for group in groups:
      text = group

      matches = re.findall(re_pos, group)
      for match in matches:
        x = num(float(match[1]) * scale_width)
        y = num(float(match[2]) * scale_height)
        scaled_pos = f"\\pos({x},{y})"
        text = text.replace(match[0], scaled_pos)

      matches = re.findall(re_move, group)
      for match in matches:
        numbers = match[1].split(",")
        numbers = [num(float(number) * scale_height) for number in numbers]
        numbers = [str(number) for number in numbers]
        scaled = "\\move({})".format(",".join(numbers))
        text = text.replace(match[0], scaled)

      matches = re.findall(re_clip, group)
      for match in matches:
        numbers = []
        for number in match[1].split(" "):
          try:
            numbers.append(num(float(number) * scale_height))
          except:
            numbers.append(number)
        numbers = [str(number) for number in numbers]
        scaled = "\\clip({})".format(" ".join(numbers))
        text = text.replace(match[0], scaled)

      for r in re_simple:
        matches = re.findall(r[0], group)
        for match in matches:
          scaled_pos = r[1].format(num(float(match[1]) * scale_height))
          text = text.replace(match[0], scaled_pos)

      event.text = event.text.replace(group, text)
