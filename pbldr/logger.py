import logging
import datetime
import re
import sys

# Prefix for logging output
PREFIX = '[>>>]'

# Documentation for ansi escape sequences.
# http://bluesock.org/~willg/dev/ansi.html#sequences
# http://en.wikipedia.org/wiki/ANSI_escape_code
# http://docs.python.org/reference/lexical_analysis.html
# `\033[` is the escape sequence character. `\033` is octal.
ATTR_CODES = {
    'bold': '1', 'italic': '3', 'strike': '9', 'underline': '4',
    'erase': '\033[K',  # Clear to the end of the line
    'reset': '\033[0m',  # All attributes off
}

FG_COLOR_CODES = {
    'black': 30, 'red': 31, 'green': 32, 'yellow': 33, 'blue': 34, 'magenta':
    35, 'cyan': 36, 'white': 37, 'default': 38,
}

BG_COLOR_CODES = {
    'bgred': 41, 'bgblack': 40, 'bggreen': 42, 'bgyellow': 43, 'bgblue': 44,
    'bgmagenta': 45, 'bgcyan': 46, 'bgwhite': 47, 'bgdefault': 49, 'bggrey':
    100,
}


class _ANSIFormatter(logging.Formatter):
    """Convert a `logging.LogReport' object into colored text, using ANSI
    escape sequences.

    """
    def format(self, record):
        mtype = ''
        if record.levelname is 'INFO':
            mtype = colorize(record.levelname + ' ', 'cyan', '', 'bold')
        elif record.levelname is 'WARNING':
            mtype = colorize(record.levelname, 'yellow', '', 'bold')
        elif record.levelname is 'ERROR':
            mtype = colorize(record.levelname, 'red', '', 'bold')
        elif record.levelname is 'CRITICAL':
            mtype = colorize(record.levelname, '', 'bgred', 'bold')
        elif record.levelname is 'DEBUG':
            mtype = colorize(record.levelname, '', 'bggrey', 'bold')
        else:
            mtype = colorize(record.levelname, 'white', '', 'bold')
        # tdate = get_time_string()
        # return OUTPUT_PREFIX + mtype + ': ' + tdate + ': ' + record.msg
        return OUTPUT_PREFIX + mtype + ': ' + record.msg


def get_time_string():
    """Returns a formatted time string.

    :returns: A formatted time string.

    """
    now = datetime.datetime.now()
    return now.strftime('%a %b %d %H:%M:%S %Y')


def _logger(text, text_attr='', note='', note_attr='', note_fgcolor='',
            note_bgcolor='', date=True, prefix=True):
    """Prints to stdout.

    _logger is responsible for making pretty output and is used throughout the
    entire program. Any whitepsace characters at the start or ends of the line
    are preserved. So lines containing '\r' will overlap. This is useful for
    progress bars and such.

    :text: The text to output.
    :text_attr: ANSI attribute to wrap text with.
    :note: String to append to the text.
    :note_attr: ANSI attribute to wrap note with.
    :note_fgcolor: Color of the appended note.
    :note_bgcolor: Background color of the note.
    :date: If true, the date will be appended.
    :prefix: If true, the date and OUTPUT_PREFIX will be displayed.

    """
    prefix = OUTPUT_PREFIX
    if date:
        prefix = prefix + get_time_string() + ': '
    if note:
        note = (colorize(note, note_fgcolor, note_bgcolor, note_attr) +
                ' ')
    pad_re = re.match(r'(\s*).*(\s*)', text)
    if pad_re:
        pre_pad = pad_re.group(1)
        pos_pad = pad_re.group(2)
    end = '\r' if text[-1] == '\r' else '\n'
    stext = text.strip()
    if text_attr:
        stext = colorize(stext, '', '', text_attr)
    output = ''.join((pre_pad, prefix, note, stext, pos_pad,
                      ATTR_CODES['reset'], end))
    sys.stdout.write(output)


def colorize(text, fgcolor, bgcolor, attr):
    """Wrap text in an ansi escape sequence, with bolding.

    :color: The color to wrap the text in.
    :text: The text to wrap.
    :attr: The attribute to wrap the text in.

    """
    fgcc = ''
    if fgcolor:
        assert(fgcolor in FG_COLOR_CODES)
        fgcc = str(FG_COLOR_CODES[fgcolor]) + ';'

    bgcc = ''
    if bgcolor:
        assert(bgcolor in BG_COLOR_CODES)
        bgcc = str(BG_COLOR_CODES[bgcolor]) + ';'

    attrc = ''
    if attr:
        assert(attr in ATTR_CODES)
        attrc = ATTR_CODES[attr] + ';'

    ccds = attrc + fgcc + bgcc
    # print('033[{}m{}{}'.format(ccds[:-1], text, ATTR_CODES['reset'][1:]))

    return '\033[{}m{}{}'.format(ccds[:-1], text, ATTR_CODES['reset'])


OUTPUT_PREFIX = colorize(PREFIX, 'cyan', '', 'bold') + ': '


def log_begin(text):
    """Logs output with [Begin] appended to the start of the string.

    :text: The message to write to stdout.

    """
    _logger(text, '', '[Begin]', 'bold', 'white', 'bgcyan')


def log_done(text):
    """Logs output with [Done] appended to the start of the string.

    :text: The message to write to stdout.

    """
    _logger(text, '', '[FINISHED]', 'bold', 'white', 'bgcyan')


def log_noprefix(text):
    """Logs output without the prefix.

    :text: The message to write to stdout.

    """
    _logger(text, date=False, prefix=False)


def log_note(text, note, fgcolor, bgcolor):
    """Logs output without the prefix.

    :text: The message to write to stdout.

    """
    assert(fgcolor in FG_COLOR_CODES)
    assert(bgcolor in BG_COLOR_CODES)
    _logger(text, '', note, 'bold', fgcolor, bgcolor)


def log(text):
    """Prints to stdout with timestap and OUTPUT_PREFIX.

    :text: The message to write to stdout.

    """
    _logger(text, date=False, prefix=True)


def getLogger(name):
    """Returns a logging object.

    :name: The name of the logger.
    :returns: logging object

    """
    return logging.getLogger(name)


def init_logging(level, logger=logging.getLogger(),
                 handler=logging.StreamHandler()):
    """Initializes the logger.

    """
    fmt = _ANSIFormatter()
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    if not level:
        level = logging.WARN
    logger.setLevel(level)
