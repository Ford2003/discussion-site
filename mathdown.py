from markupsafe import Markup
from flask import Blueprint, current_app, url_for


class _mathdown(object):
    def html_head(self):
        html = Markup(''' <script type="text/x-mathjax-config">
	MathJax.Hub.Config({"HTML-CSS": { preferredFont: "TeX", availableFonts: ["STIX","TeX"], linebreaks: { automatic:true }, EqnChunk: (MathJax.Hub.Browser.isMobile ? 10 : 50) },
		tex2jax: { inlineMath: [ ["$", "$"], ["\\\\(","\\\\)"] ], displayMath: [ ["$$","$$"], ["\\[", "\\]"] ], processEscapes: true, ignoreClass: "tex2jax_ignore|dno" },
        TeX: {noErrors: {disabled: true}}
 });
 </script>
 <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-AMS_HTML-full"></script>
 <script src="https://cdnjs.cloudflare.com/ajax/libs/markdown-it/12.2.0/markdown-it.js" 
integrity="sha512-ivJskyHEWoa1WrFlVDWM7o8I7ZKt2dF97kUVMKHT4CPSWxZ7VHuCydjiED3pjOpN0WuT2XA3pK4HrZYNsZ4OqA==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
 ''')
        html += Markup('<script type="text/javascript" src="' + url_for('static',
                                                                         filename='Markdown.Converter.js') + '"></script>\n')
        html += Markup(
            '<script type="text/javascript" src="//cdnjs.cloudflare.com/ajax/libs/pagedown/1.0/Markdown.Sanitizer.min.js"></script>\n')
        return html

    def include_mathdown_editor(self):
        html = self.html_head()
        html += Markup(
            ' <script type="text/javascript" src="//cdnjs.cloudflare.com/ajax/libs/pagedown/1.0/Markdown.Editor.min.js"></script>\n')
        html += Markup(
            ' <link rel="stylesheet" type="text/css" href="' + url_for('static', filename='wmd.css') + '">\n')
        html += Markup(' <script src="' + url_for('static', filename='mathjax-editing.js') + '"></script>')
        return html

    def include_mathdown(self):
        html = self.html_head()
        html += Markup(''' <script type="text/javascript">
                            var md = window.markdownit();
                            window.addEventListener("load", function () {
                                var x = document.getElementsByClassName("mathdown");
                                for (var i = 0; i < x.length; i++) {
                                    var text = x[i].textContent;
                                    x[i].innerHTML = md.render(text);
                                    MathJax.Hub.Queue(["Typeset", MathJax.Hub, x[i]]);
                                }
                            });
                         </script>
                         ''')
        return html

    def include_mathdown_all(self):
        html = self.html_head()
        html += Markup(
            '<script type="text/javascript" src="//cdnjs.cloudflare.com/ajax/libs/pagedown/1.0/Markdown.Editor.min.js"></script>\n')
        html += Markup(
            '<link rel="stylesheet" type="text/css" href="' + url_for('static', filename='wmd.css') + '">\n')
        html += Markup('<script src="' + url_for('static', filename='mathjax-editing.js') + '"></script>\n')
        html += Markup('''<script type="text/javascript">
                            var md1 = window.markdownit();
                            window.addEventListener("load", function () {
                                var x = document.getElementsByClassName("mathdown");
                                for (var i = 0; i < x.length; i++) {
                                    var text = x[i].textContent;
                                    x[i].innerHTML = md1.render(text);
                                    MathJax.Hub.Queue(["Typeset", MathJax.Hub, x[i]]);
                                }
                            });
                         </script>
                         ''')
        return html



class MathDown(object):
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['mathdown'] = _mathdown()
        app.context_processor(self.context_processor)
        blueprint = Blueprint(
            'mathdown',
            __name__,
            template_folder='templates',
            static_folder='static',
            static_url_path=app.static_url_path + '/mathdown')

        app.register_blueprint(blueprint)

    @staticmethod
    def context_processor():
        return {'mathdown': current_app.extensions['mathdown']}
