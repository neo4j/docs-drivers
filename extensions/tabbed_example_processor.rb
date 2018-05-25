require 'asciidoctor/extensions'

class TabbedExampleProcessor < Asciidoctor::Extensions::Treeprocessor

  def process document
    document.find_by(context: :example, role: "tabbed-example").each do |block|
      block.blocks.delete_if { |candidate|
        role = candidate.attributes.fetch("role", "defaultroleforblock")
        role["include-with-"] and !document.attributes[role]
      }
    end
  end

end
