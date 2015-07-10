#!/usr/bin/python

from __future__ import print_function
import os, sys, time, argparse, json
import uuid

BASE="/opt/deepdream"
IN_PATH="/content/input"
OUT_PATH="/content/output"
IN="{}/{}".format(BASE, IN_PATH)
OUT="{}/{}".format(BASE, OUT_PATH)
json_data = {}

LAYER=['inception_4c/output']

def get_settings():
  global LAYER
  with open("/opt/deepdream/settings.json") as json_file:
    json_data = json.load(json_file)
    if json_data.get('layer'):
      LAYER=json_data.get('layer', [])
get_settings()

def create_dirs():
  for path in [IN, OUT]:
    if not os.path.exists(path):
      os.mkdir(path)

def get_paths(name):
  return {
    'in': os.path.join(IN, name),
    'out': os.path.join(OUT, name),
  }

def process_image(name):
  loc = name.rfind(".")
  name_short = name[:loc]
  exten = name[loc+1:]
  for layer in LAYER:
    fname = get_paths(name)
    tmp_in = "/tmp/input.{}".format(exten)
    tmp_out = "/tmp/output.{}".format(exten)
    os.system("cp {} {}".format(fname['in'], tmp_in, exten))
    if not os.path.exists(tmp_in):
      print("No input path {}".format(tmp_in))
      continue
    print("Processing {} - {}".format(fname['in'], layer))
    ret = os.system("cd {}; ./deepdream.py {} {} -l {}".format(BASE, tmp_in, tmp_out, layer))
    if ret != 0:
      print("Failed to process {}, ret: {}".format(name, ret))
      break
    unique = "{}.{}".format(uuid.uuid4(), time.time())
    out_dir = "{}/{}".format(OUT, unique)
    os.mkdir(out_dir)
    info = {
      'name': name_short[:10],
      'layer': layer,
      'out': '/content/output/{}/output.{}'.format(unique, exten),
      'orig': '/content/output/{}/orig.{}'.format(unique, exten),
    }
    with open('{}/info.json'.format(out_dir), 'w') as f:
      f.write(json.dumps(info))

    os.system("cp {} {}/orig.{}; chmod 644 {}/orig.{}".format(tmp_in, out_dir, exten, out_dir, exten))
    os.system("cp {} {}/output.{}".format(tmp_out, out_dir, exten))
    print("Done with {} in {}".format(name, out_dir))
  os.system("rm {}".format(fname['in']))

def process_images():
  """Go through the input directory and process the images

  1. If we find an image in the IN directory process via deepdream.py
  2. Copy it from IN to the ORIG directory
  3. Remove the file
  """
  create_dirs()
  for root, dirs, files in os.walk(IN):
    for name in files:
      if name[0] == '.':
        continue
      process_image(name)

def ap_process_loop(args):
  while True:
    get_settings()
    process_images()
    time.sleep(1)

def ap_process_once(args):
  process_images()

def generate_json():
  img_list = []
  counter = 0
  for root, dirs, files in os.walk(OUT):
    for d_name in dirs:
      info = "{}/info.json".format(os.path.join(OUT, d_name))
      if d_name and os.path.exists(info):
        counter += 1
        with open(info, 'r') as f:
          obj = json.load(f)
          obj['id'] = counter
          img_list.append(obj)
  with open('{}/content/images.json'.format(BASE), 'w') as f:
    f.write(json.dumps(img_list))

def ap_json(args):
  """Generate images.json"""
  create_dirs()
  while True:
    generate_json()
    time.sleep(5)

def ap_check(args):
  for root, dirs, files in os.walk(OUT):
    if not files:
      continue
    d_name = os.path.basename(root)
    for item in ['info.json', 'orig.', 'output.']:
      ret = [f_name.find(item) for f_name in files]
      if 0 not in ret:
        print("INVALID: {} - no {} found".format(d_name, item))
        if args.remove_invalid:
          print("Removing {}".format(root))
          os.system("rm -rf {}".format(root))
        break

if __name__ == "__main__":
  def add_sp(sub_p, action, func=None, help=None):
    p = sub_p.add_parser(action, help=help)
    if func:
      p.set_defaults(func=func)
    return p

  parser = argparse.ArgumentParser(description = 'Cloud Dream Runner')
  sub_p = parser.add_subparsers(title='Actions',
                                help='%(prog)s <action> -h for more info')
  p = add_sp(sub_p, 'process_loop', func=ap_process_loop,
    help='Process new images forever')
  p = add_sp(sub_p, 'process_once', func=ap_process_once,
    help='Process images onces')
  p = add_sp(sub_p, 'json', func=ap_json,
    help='Continually update json')
  p = add_sp(sub_p, 'check', func=ap_check,
    help='Check various information')
  p.add_argument('--remove-invalid', action='store_true',
                 help='Remove invalid directories')
  args = parser.parse_args()
  args.func(args)
