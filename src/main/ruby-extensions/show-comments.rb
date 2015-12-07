require 'asciidoctor'
require 'asciidoctor/extensions'

include Asciidoctor

class ShowComments < Asciidoctor::Extensions::Preprocessor
  def process document, reader
    if document.attr? 'showcomments'
      Reader.new reader.readlines.map { |l|
        if (l.start_with? '// TODO ') || (l.start_with? '// FIXME ') || (l.start_with? '// TODO:') || (l.start_with? '// FIXME:')
          %([comment]###{l[3..-1]}##)
        else
          l
        end
      }
    else
      reader
    end
  end
end

