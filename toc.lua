function Div(el)
  if el.classes:includes("toc") then
    return pandoc.RawBlock(
      "latex",
      "\\vfill\n\\tableofcontents"
    )
  end
end