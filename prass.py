#!/usr/bin/env python2
import click
import sys
from operator import attrgetter
from common import PrassError
from subs import AssScript
from tools import Timecodes, parse_keyframes

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    pass


@cli.command("convert-srt", short_help="convert srt subtitles to ass")
@click.option("-o", "--output", "output_file", default='-', type=click.File(encoding="utf-8-sig", mode='w'))
@click.option("--encoding", "encoding", default='utf-8-sig')
@click.argument("input_path", type=click.Path(dir_okay=False))
def convert_srt(input_path, output_file, encoding):
    try:
        with click.open_file(input_path, encoding=encoding) as input_file:
            AssScript.from_srt_stream(input_file).to_ass_stream(output_file)
    except LookupError:
        raise PrassError("Encoding {0} doesn't exist".format(encoding))


@cli.command('copy-styles', short_help="copy stiles from one ass script to another")
@click.option("-o", "--output", "output_file", default="-", type=click.File(encoding="utf-8-sig", mode='w'))
@click.option('--to', 'dst_file', required=True, type=click.File(encoding='utf-8-sig', mode='r'),
              help="File to copy the styles to. Will be rewritten so you might want to backup.")
@click.option('--from', 'src_file', required=True, type=click.File(encoding='utf-8-sig', mode='r'),
              help="File to take the styles from")
@click.option('--clean', default=False, is_flag=True,
              help="Remove all older styles in the destination file")
def copy_styles(dst_file, src_file, output_file, clean):
    src_script = AssScript.from_ass_stream(src_file)
    dst_script = AssScript.from_ass_stream(dst_file)

    dst_script.append_styles(src_script.styles, clean=clean)
    dst_script.to_ass_stream(output_file)


@cli.command('sort', short_help="sort ass script events")
@click.option("-o", "--output", "output_file", default='-', type=click.File(encoding="utf-8-sig", mode='w'), metavar="<path>")
@click.argument("input_file", type=click.File(encoding="utf-8-sig"))
@click.option('--by', 'sort_by', multiple=True, default=['start'], help="Parameter to sort by",
              type=click.Choice(['time', 'start', 'end', 'style', 'actor', 'effect', 'layer']))
@click.option('--desc', 'descending', default=False, is_flag=True, help="Descending order")
def sort_script(input_file, output_file, sort_by, descending):
    script = AssScript.from_ass_stream(input_file)
    attrs_map = {
        "start": "start",
        "time": "start",
        "end": "end",
        "style": "style",
        "actor": "actor",
        "effect": "effect",
        "layer": "layer"
    }
    getter = attrgetter(*[attrs_map[x] for x in sort_by])
    script.sort_events(getter, descending)
    script.to_ass_stream(output_file)


@cli.command('tpp', short_help="timing post-processor")
@click.option("-o", "--output", "output_file", default='-', type=click.File(encoding="utf-8-sig", mode='w'), metavar="<path>")
@click.argument("input_file", type=click.File(encoding="utf-8-sig"))
@click.option("-s", "--style", "styles", multiple=True, metavar="<names>",
              help="Style names to process. All by default. Use comma to separate, or supply it multiple times")
@click.option("--lead-in", "lead_in", default=0, type=int, metavar="<ms>",
              help="Lead-in value in milliseconds")
@click.option("--lead-out", "lead_out", default=0, type=int, metavar="<ms>",
              help="Lead-out value in milliseconds")
@click.option("--overlap", "max_overlap", default=0, type=int, metavar="<ms>",
              help="Maximum overlap for two lines to be made continuous, in milliseconds")
@click.option("--gap", "max_gap", default=0, type=int, metavar="<ms>",
              help="Maximum gap between two lines to be made continuous, in milliseconds")
@click.option("--bias", "adjacent_bias", default=50, type=click.IntRange(0, 100), metavar="<percent>",
              help="How to set the adjoining of lines. "
                   "0 - change start time of the second line, 100 - end time of the first line. "
                   "Values from 0 to 100 allowed.")
@click.option("--keyframes", "keyframes_path", type=click.Path(exists=True, readable=True, dir_okay=False), metavar="<path>",
              help="Path to keyframes file")
@click.option("--timecodes", "timecodes_path", type=click.Path(readable=True, dir_okay=False), metavar="<path>",
              help="Path to timecodes file")
@click.option("--fps", "fps", type=float, metavar="<float>",
              help="Fps provided as float value, in case you don't have timecodes")
@click.option("--kf-before-start", default=0, type=float, metavar="<ms>",
              help="Max distance between a keyframe and event start for it to be snapped, when keyframe is placed before the event")
@click.option("--kf-after-start", default=0, type=float, metavar="<ms>",
              help="Max distance between a keyframe and event start for it to be snapped, when keyframe is placed after the start time")
@click.option("--kf-before-end", default=0, type=float, metavar="<ms>",
              help="Max distance between a keyframe and event end for it to be snapped, when keyframe is placed before the end time")
@click.option("--kf-after-end", default=0, type=float, metavar="<ms>",
              help="Max distance between a keyframe and event end for it to be snapped, when keyframe is placed after the event")
def tpp(input_file, output_file, styles, lead_in, lead_out, max_overlap, max_gap, adjacent_bias,
        keyframes_path, timecodes_path, fps, kf_before_start, kf_after_start, kf_before_end, kf_after_end):

    if fps and timecodes_path:
        raise PrassError('Timecodes file and fps cannot be specified at the same time')
    if fps:
        timecodes = Timecodes.cfr(fps)
    elif timecodes_path:
        timecodes = Timecodes.from_file(timecodes_path)
    elif any((kf_before_start, kf_after_start, kf_before_end, kf_after_end)):
        raise PrassError('You have to provide either fps or timecodes file for keyframes processing')
    else:
        timecodes = None

    if timecodes and not keyframes_path:
        raise PrassError('You have to specify keyframes file for keyframes processing')

    keyframes_list = parse_keyframes(keyframes_path) if keyframes_path else None

    actual_styles = []
    for style in styles:
        actual_styles.extend(x.strip() for x in style.split(','))

    script = AssScript.from_ass_stream(input_file)
    script.tpp(actual_styles, lead_in, lead_out, max_overlap, max_gap, adjacent_bias,
               keyframes_list, timecodes, kf_before_start, kf_after_start, kf_before_end, kf_after_end)
    script.to_ass_stream(output_file)


@cli.command("cleanup")
@click.option("-o", "--output", "output_file", default='-', type=click.File(encoding="utf-8-sig", mode='w'), metavar="<path>")
@click.argument("input_file", type=click.File(encoding="utf-8-sig"))
@click.option("--comments", "drop_comments", default=False, is_flag=True,
              help="Remove commented lines")
@click.option("--empty-lines", "drop_empty_lines", default=False, is_flag=True,
              help="Remove empty lines")
@click.option("--styles", "drop_unused_styles", default=False, is_flag=True,
              help="Remove unused styles")
@click.option("--actors", "drop_actors", default=False, is_flag=True,
              help="Remove actor field")
@click.option("--effects", "drop_effects", default=False, is_flag=True,
              help="Remove effects field")
def cleanup(input_file, output_file, drop_comments, drop_empty_lines, drop_unused_styles, drop_actors, drop_effects):
    script = AssScript.from_ass_stream(input_file)
    script.cleanup(drop_comments, drop_empty_lines, drop_unused_styles, drop_actors, drop_effects)
    script.to_ass_stream(output_file)

if __name__ == '__main__':
    try:
        default_map = {}
        if not sys.stdin.isatty():
            for command, arg_name in (("convert-srt", "input_path"), ("copy-styles", "dst_file"),
                                      ("sort", "input_file"), ("tpp", "input_file")):
                default_map[command] = {arg_name: '-'}

        cli(default_map=default_map)
    except PrassError as e:
        click.echo(e.message)
