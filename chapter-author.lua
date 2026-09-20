function Header(el)
  -- Seulement les titres ## avec un attribut author
  if el.level ~= 2 then
    return nil
  end

  local author = el.attributes["author"]

  if not author or author == "" then
    return nil
  end

  local title = pandoc.utils.stringify(el.content)

  -- Échappement LaTeX minimal
  local function latex_escape(s)
    s = s:gsub("\\", "\\textbackslash{}")
    s = s:gsub("([%%#$&_{}])", "\\%1")
    return s
  end

  title = latex_escape(title)
  author = latex_escape(author)

  local latex = string.format(
    "\\chapter[%s \\textit{par %s}]{%s}\n\n" ..
    "\\chapterrunninghead{%s}\n" ..    
    "{\\large\\itshape par %s\\par}\n",
    title,
    author,
    title,
    author,
    author
  )

  return pandoc.RawBlock("latex", latex)
end