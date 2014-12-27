"""
A module for converting numbers or color arguments to *RGB* or *RGBA*

*RGB* and *RGBA* are sequences of, respectively, 3 or 4 floats in the
range 0-1.

This module includes functions and classes for color specification
conversions, and for mapping numbers to colors in a 1-D array of colors called
a colormap. Colormapping typically involves two steps: a data array is first
mapped onto the range 0-1 using an instance of :class:`Normalize` or of a
subclass; then this number in the 0-1 range is mapped to a color using an
instance of a subclass of :class:`Colormap`.  Two are provided here:
:class:`LinearSegmentedColormap`, which is used to generate all the built-in
colormap instances, but is also useful for making custom colormaps, and
:class:`ListedColormap`, which is used for generating a custom colormap from a
list of color specifications.

The module also provides a single instance, *colorConverter*, of the
:class:`ColorConverter` class providing methods for converting single color
specifications or sequences of them to *RGB* or *RGBA*.

Commands which take color arguments can use several formats to specify
the colors.  For the basic built-in colors, you can use a single letter

    - b: blue
    - g: green
    - r: red
    - c: cyan
    - m: magenta
    - y: yellow
    - k: black
    - w: white

Gray shades can be given as a string encoding a float in the 0-1 range, e.g.::

    color = '0.75'

For a greater range of colors, you have two options.  You can specify the
color using an html hex string, as in::

      color = '#eeefff'

or you can pass an *R* , *G* , *B* tuple, where each of *R* , *G* , *B* are in
the range [0,1].

Finally, legal html names for colors, like 'red', 'burlywood' and 'chartreuse'
are supported.
"""
from __future__ import print_function, division
import re

cnames = {
    'aliceblue':            '#F0F8FF',
    'antiquewhite':         '#FAEBD7',
    'aqua':                 '#00FFFF',
    'aquamarine':           '#7FFFD4',
    'azure':                '#F0FFFF',
    'beige':                '#F5F5DC',
    'bisque':               '#FFE4C4',
    'black':                '#000000',
    'blanchedalmond':       '#FFEBCD',
    'blue':                 '#0000FF',
    'blueviolet':           '#8A2BE2',
    'brown':                '#A52A2A',
    'burlywood':            '#DEB887',
    'cadetblue':            '#5F9EA0',
    'chartreuse':           '#7FFF00',
    'chocolate':            '#D2691E',
    'coral':                '#FF7F50',
    'cornflowerblue':       '#6495ED',
    'cornsilk':             '#FFF8DC',
    'crimson':              '#DC143C',
    'cyan':                 '#00FFFF',
    'darkblue':             '#00008B',
    'darkcyan':             '#008B8B',
    'darkgoldenrod':        '#B8860B',
    'darkgray':             '#A9A9A9',
    'darkgreen':            '#006400',
    'darkkhaki':            '#BDB76B',
    'darkmagenta':          '#8B008B',
    'darkolivegreen':       '#556B2F',
    'darkorange':           '#FF8C00',
    'darkorchid':           '#9932CC',
    'darkred':              '#8B0000',
    'darksalmon':           '#E9967A',
    'darkseagreen':         '#8FBC8F',
    'darkslateblue':        '#483D8B',
    'darkslategray':        '#2F4F4F',
    'darkturquoise':        '#00CED1',
    'darkviolet':           '#9400D3',
    'deeppink':             '#FF1493',
    'deepskyblue':          '#00BFFF',
    'dimgray':              '#696969',
    'dodgerblue':           '#1E90FF',
    'firebrick':            '#B22222',
    'floralwhite':          '#FFFAF0',
    'forestgreen':          '#228B22',
    'fuchsia':              '#FF00FF',
    'gainsboro':            '#DCDCDC',
    'ghostwhite':           '#F8F8FF',
    'gold':                 '#FFD700',
    'goldenrod':            '#DAA520',
    'gray':                 '#808080',
    'green':                '#008000',
    'greenyellow':          '#ADFF2F',
    'honeydew':             '#F0FFF0',
    'hotpink':              '#FF69B4',
    'indianred':            '#CD5C5C',
    'indigo':               '#4B0082',
    'ivory':                '#FFFFF0',
    'khaki':                '#F0E68C',
    'lavender':             '#E6E6FA',
    'lavenderblush':        '#FFF0F5',
    'lawngreen':            '#7CFC00',
    'lemonchiffon':         '#FFFACD',
    'lightblue':            '#ADD8E6',
    'lightcoral':           '#F08080',
    'lightcyan':            '#E0FFFF',
    'lightgoldenrodyellow': '#FAFAD2',
    'lightgreen':           '#90EE90',
    'lightgray':            '#D3D3D3',
    'lightpink':            '#FFB6C1',
    'lightsalmon':          '#FFA07A',
    'lightseagreen':        '#20B2AA',
    'lightskyblue':         '#87CEFA',
    'lightslategray':       '#778899',
    'lightsteelblue':       '#B0C4DE',
    'lightyellow':          '#FFFFE0',
    'lime':                 '#00FF00',
    'limegreen':            '#32CD32',
    'linen':                '#FAF0E6',
    'magenta':              '#FF00FF',
    'maroon':               '#800000',
    'mediumaquamarine':     '#66CDAA',
    'mediumblue':           '#0000CD',
    'mediumorchid':         '#BA55D3',
    'mediumpurple':         '#9370DB',
    'mediumseagreen':       '#3CB371',
    'mediumslateblue':      '#7B68EE',
    'mediumspringgreen':    '#00FA9A',
    'mediumturquoise':      '#48D1CC',
    'mediumvioletred':      '#C71585',
    'midnightblue':         '#191970',
    'mintcream':            '#F5FFFA',
    'mistyrose':            '#FFE4E1',
    'moccasin':             '#FFE4B5',
    'navajowhite':          '#FFDEAD',
    'navy':                 '#000080',
    'oldlace':              '#FDF5E6',
    'olive':                '#808000',
    'olivedrab':            '#6B8E23',
    'orange':               '#FFA500',
    'orangered':            '#FF4500',
    'orchid':               '#DA70D6',
    'palegoldenrod':        '#EEE8AA',
    'palegreen':            '#98FB98',
    'paleturquoise':        '#AFEEEE',
    'palevioletred':        '#DB7093',
    'papayawhip':           '#FFEFD5',
    'peachpuff':            '#FFDAB9',
    'peru':                 '#CD853F',
    'pink':                 '#FFC0CB',
    'plum':                 '#DDA0DD',
    'powderblue':           '#B0E0E6',
    'purple':               '#800080',
    'red':                  '#FF0000',
    'rosybrown':            '#BC8F8F',
    'royalblue':            '#4169E1',
    'saddlebrown':          '#8B4513',
    'salmon':               '#FA8072',
    'sandybrown':           '#FAA460',
    'seagreen':             '#2E8B57',
    'seashell':             '#FFF5EE',
    'sienna':               '#A0522D',
    'silver':               '#C0C0C0',
    'skyblue':              '#87CEEB',
    'slateblue':            '#6A5ACD',
    'slategray':            '#708090',
    'snow':                 '#FFFAFA',
    'springgreen':          '#00FF7F',
    'steelblue':            '#4682B4',
    'tan':                  '#D2B48C',
    'teal':                 '#008080',
    'thistle':              '#D8BFD8',
    'tomato':               '#FF6347',
    'turquoise':            '#40E0D0',
    'violet':               '#EE82EE',
    'wheat':                '#F5DEB3',
    'white':                '#FFFFFF',
    'whitesmoke':           '#F5F5F5',
    'yellow':               '#FFFF00',
    'yellowgreen':          '#9ACD32'}


# add british equivs
for k, v in cnames.items():
    if k.find('gray') >= 0:
        k = k.replace('gray', 'grey')
        cnames[k] = v


def hex2color(s):
    """
    Take a hex string *s* and return the corresponding rgb 3-tuple
    Example: #efefef -> (0.93725, 0.93725, 0.93725)
    """
    if not isinstance(s, basestring):
        raise TypeError('hex2color requires a string argument')
    if hexColorPattern.match(s) is None:
        raise ValueError('invalid hex color string "%s"' % s)
    return tuple([int(n, 16) / 255.0 for n in (s[1:3], s[3:5], s[5:7])])


def rgb2hex(rgb):
    'Given an rgb or rgba sequence of 0-1 floats, return the hex string'
    return '#%02x%02x%02x' % tuple([np.round(val * 255) for val in rgb[:3]])


class ColorConverter(object):
    """
    Provides methods for converting color specifications to *RGB* or *RGBA*

    Caching is used for more efficient conversion upon repeated calls
    with the same argument.

    Ordinarily only the single instance instantiated in this module,
    *colorConverter*, is needed.
    """
    colors = {
        'b': (0.0, 0.0, 1.0),
        'g': (0.0, 0.5, 0.0),
        'r': (1.0, 0.0, 0.0),
        'c': (0.0, 0.75, 0.75),
        'm': (0.75, 0, 0.75),
        'y': (0.75, 0.75, 0),
        'k': (0.0, 0.0, 0.0),
        'w': (1.0, 1.0, 1.0), }

    cache = {}

    def to_rgb(self, arg):
        """
        Returns an *RGB* tuple of three floats from 0-1.

        *arg* can be an *RGB* or *RGBA* sequence or a string in any of
        several forms:

            1) a letter from the set 'rgbcmykw'
            2) a hex color string, like '#00FFFF'
            3) a standard name, like 'aqua'
            4) a float, like '0.4', indicating gray on a 0-1 scale

        if *arg* is *RGBA*, the *A* will simply be discarded.
        """
        try:
            return self.cache[arg]
        except KeyError:
            pass
        except TypeError:  # could be unhashable rgb seq
            arg = tuple(arg)
            try:
                return self.cache[arg]
            except KeyError:
                pass
            except TypeError:
                raise ValueError(
                    'to_rgb: arg "%s" is unhashable even inside a tuple'
                    % (str(arg),))

        try:
            if isinstance(arg,basestring):
                argl = arg.lower()
                color = self.colors.get(argl, None)
                if color is None:
                    str1 = cnames.get(argl, argl)
                    if str1.startswith('#'):
                        color = hex2color(str1)
                    else:
                        fl = float(argl)
                        if fl < 0 or fl > 1:
                            raise ValueError(
                                'gray (string) must be in range 0-1')
                        color = tuple([fl] * 3)
            elif hasattr(arg,'__iter__'):
                if len(arg) > 4 or len(arg) < 3:
                    raise ValueError(
                        'sequence length is %d; must be 3 or 4' % len(arg))
                color = tuple(arg[:3])
                if [x for x in color if (float(x) < 0) or (x > 1)]:
                    # This will raise TypeError if x is not a number.
                    raise ValueError(
                        'number in rbg sequence outside 0-1 range')
            else:
                raise ValueError(
                    'cannot convert argument to rgb sequence')

            self.cache[arg] = color

        except (KeyError, ValueError, TypeError) as exc:
            raise ValueError(
                'to_rgb: Invalid rgb arg "%s"\n%s' % (str(arg), exc))
            # Error messages could be improved by handling TypeError
            # separately; but this should be rare and not too hard
            # for the user to figure out as-is.
        return color

    def to_rgba(self, arg, alpha=None):
        """
        Returns an *RGBA* tuple of four floats from 0-1.

        For acceptable values of *arg*, see :meth:`to_rgb`.
        In addition, if *arg* is "none" (case-insensitive),
        then (0,0,0,0) will be returned.
        If *arg* is an *RGBA* sequence and *alpha* is not *None*,
        *alpha* will replace the original *A*.
        """
        try:
            if arg.lower() == 'none':
                return (0.0, 0.0, 0.0, 0.0)
        except AttributeError:
            pass

        try:
            if not isinstance(arg,basestring) and hasattr(arg,'__iter__'):
                if len(arg) == 4:
                    if [x for x in arg if (float(x) < 0) or (x > 1)]:
                        # This will raise TypeError if x is not a number.
                        raise ValueError(
                            'number in rbga sequence outside 0-1 range')
                    if alpha is None:
                        return tuple(arg)
                    if alpha < 0.0 or alpha > 1.0:
                        raise ValueError("alpha must be in range 0-1")
                    return arg[0], arg[1], arg[2], alpha
                r, g, b = arg[:3]
                if [x for x in (r, g, b) if (float(x) < 0) or (x > 1)]:
                    raise ValueError(
                        'number in rbg sequence outside 0-1 range')
            else:
                r, g, b = self.to_rgb(arg)
            if alpha is None:
                alpha = 1.0
            return r, g, b, alpha
        except (TypeError, ValueError) as exc:
            raise ValueError(
                'to_rgba: Invalid rgba arg "%s"\n%s' % (str(arg), exc))
