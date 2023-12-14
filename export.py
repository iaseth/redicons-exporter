import json
import os

from bs4 import BeautifulSoup


ICON_PACKS = [
	{"name": "Bootstrap", "prefix": "bs", "path": "icons/bootstrap-icons"},
	{"name": "Material Icons Filled", "prefix": "gmf", "path": "icons/material-icons/filled"},
	{"name": "Material Icons Outlined", "prefix": "gmo", "path": "icons/material-icons/outlined"},
	{"name": "Material Icons Round", "prefix": "gmr", "path": "icons/material-icons/round"},
	{"name": "Material Icons Sharp", "prefix": "gms", "path": "icons/material-icons/sharp"},
	{"name": "Material Icons Two-tone", "prefix": "gm2", "path": "icons/material-icons/two-tone"},
]

OUTPUT_JSON_PATH = "out/redicons.full.json"
OUTPUT_MIN_JSON_PATH = "out/redicons.min.json"
OUTPUT_NAMES_JSON_PATH = "out/iconnames.json"

KNOWN_TAGS = [
	{"name": "path", "knownAttrs": ["d", "fill-rule", "fill-opacity", "opacity"]},
	{"name": "symbol", "knownAttrs": ["id", "class", "viewbox"]},
	{"name": "circle", "knownAttrs": ["cx", "cy", "r", "fill-rule", "opacity"]},
	{"name": "ellipse", "knownAttrs": ["cx", "cy", "rx", "ry", "opacity"]},
	{"name": "rect", "knownAttrs": ["width", "height", "x", "y", "rx", "ry", "transform"]}
]
KNOWN_TAG_NAMES = [tag["name"] for tag in KNOWN_TAGS]
IGNORED_ATTRS = ["class"]

BETTER_ATTR_NAMES = {
	"class": "className",
	"fill-rule": "fillRule",
	"fill-opacity": "fillOpacity",
}

def verify_svg_and_get_tags(svg_filepath):
	with open(svg_filepath) as f:
		soup = BeautifulSoup(f.read(), "lxml")

	svg_tags = soup.find_all("svg")
	if len(svg_tags) != 1:
		print(f"Should have exactly one SVG tag: {len(svg_tags)}")
		return False

	svg_tag = svg_tags[0]
	className = " ".join(svg_tag.attrs["class"]) if "class" in svg_tag.attrs else ""

	tags = svg_tag.find_all()
	for tag in tags:
		if tag.name not in KNOWN_TAG_NAMES:
			print(f"\t\t[TAG] Unknown tag found: {tag.name} ({svg_filepath})")
			return False

		knownAttrs = []
		for known_tag in KNOWN_TAGS:
			if known_tag["name"] == tag.name:
				knownAttrs = known_tag["knownAttrs"]

		for attr in tag.attrs:
			if attr not in knownAttrs:
				print(f"\t\t\t[ATTR] Unknown '{tag.name}' attr found: '{attr}' ({svg_filepath})")
				return False

	return tags, className


def get_attr_name(attr):
	if attr in BETTER_ATTR_NAMES:
		return BETTER_ATTR_NAMES[attr]
	return attr


def get_tag_object(tag):
	jo = {}
	for attr in tag.attrs:
		if attr not in IGNORED_ATTRS:
			attr_name = get_attr_name(attr)
			jo[attr_name] = tag.attrs[attr]
	return jo


def get_icons_from_icon_pack(icon_pack):
	prefix = icon_pack['prefix']
	svg_dirpath = icon_pack['path']
	files = os.listdir(svg_dirpath)
	svg_filenames = [file for file in files if file.endswith(".svg")]

	icons = []
	for idx, svg_filename in enumerate(svg_filenames):
		# print(f"{idx+1:4} => {svg_filename}")
		svg_filepath = os.path.join(svg_dirpath, svg_filename)
		retval = verify_svg_and_get_tags(svg_filepath)
		if not retval:
			print(f"\tSVG contains unknown Tags or Attributes: ({svg_filepath})")
			continue

		# every pack has a suffux
		icon_name = f"{prefix}-{svg_filename[:-4]}"
		# material icons had underscores, replaces them with a dash
		icon_name = icon_name.replace("_", "-")

		tags, className = retval
		icon = {}
		icon["name"] = icon_name
		icon["className"] = className
		icon["paths"] = [get_tag_object(tag) for tag in tags if tag.name == "path"]
		icon["symbols"] = [get_tag_object(tag) for tag in tags if tag.name == "symbol"]
		icon["circles"] = [get_tag_object(tag) for tag in tags if tag.name == "circle"]
		icon["ellipses"] = [get_tag_object(tag) for tag in tags if tag.name == "ellipse"]
		icon["rects"] = [get_tag_object(tag) for tag in tags if tag.name == "rect"]
		icons.append(icon)
		# break
	return icons


def main():
	icons = []
	print(f"Looking through {len(ICON_PACKS)} icon packs:")
	for idx, icon_pack in enumerate(ICON_PACKS):
		icons_in_current_pack = get_icons_from_icon_pack(icon_pack)
		icons.extend(icons_in_current_pack)
		print(f"\t{idx+1}. Added {len(icons_in_current_pack)} icons from {icon_pack['name']}")

	jo = {}
	jo["icons"] = icons
	with open(OUTPUT_JSON_PATH, "w") as f:
		json.dump(jo, f, indent="\t")
	print(f"Saved: {OUTPUT_JSON_PATH} ({len(icons)} icons)")

	# some cleanup to minimize the size of npm package
	array_names = ["paths", "symbols", "circles", "ellipses", "rects"]
	for icon in icons:
		del icon["className"] # delete className as not needed
		for array_name in array_names:
			if len(icon[array_name]) == 0:
				del icon[array_name] # delete empty arrays

	with open(OUTPUT_MIN_JSON_PATH, "w") as f:
		json.dump(jo, f, indent="\t")
	print(f"Saved: {OUTPUT_MIN_JSON_PATH} ({len(icons)} optimal icons)")

	namesJson = {}
	namesJson["iconNames"] = [icon["name"] for icon in icons]
	with open(OUTPUT_NAMES_JSON_PATH, "w") as f:
		json.dump(namesJson, f, indent="\t")
	print(f"Saved: {OUTPUT_NAMES_JSON_PATH} ({len(icons)} icon names)")


if __name__ == "__main__":
	main()
