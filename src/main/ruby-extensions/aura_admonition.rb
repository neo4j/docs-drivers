require 'asciidoctor/extensions'

class AuraAdmonition < Asciidoctor::Extensions::BlockProcessor

  use_dsl

  named :AURA
  on_contexts :example, :paragraph, :open

  def process parent, reader, attrs
    attrs['name'] = 'caution'
    attrs['caption'] = 'Aura'
    attrs['role'] = 'aura'
    block = create_block parent, :admonition, reader.lines, attrs, content_model: :compound
  end

end
