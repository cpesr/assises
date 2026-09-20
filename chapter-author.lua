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
  local identifier = el.identifier

  -- Échappement LaTeX minimal
  local function latex_escape(s)
    s = s:gsub("\\", "\\textbackslash{}")
    s = s:gsub("([%%#$&_{}])", "\\%1")
    return s
  end

  title = latex_escape(title)
  author = latex_escape(author)

  -- Construction du chapitre.
  --
  -- L'argument optionnel de \chapter est utilisé dans la TOC :
  --   Titre par Auteur
  --
  -- L'argument principal est utilisé dans le corps :
  --   Titre
  local chapter = string.format(
    "\\chapter[%s \\textit{par %s}]{%s}",
    title,
    author,
    title
  )

  -- On conserve l'identifiant généré par Pandoc.
  -- Sans cela, remplacer le Header par un RawBlock fait perdre
  -- l'ancre que Pandoc aurait normalement créée.
  if identifier and identifier ~= "" then
    chapter = string.format(
      "\\hypertarget{%s}{%%\n%s\\label{%s}}",
      identifier,
      chapter,
      identifier
    )
  end

  -- Auteur affiché sous le titre du chapitre
  local author_line = string.format(
    "{\\large\\itshape par %s\\par}",
    author
  )

  -- Assemblage final
  local latex = chapter
    .. "\n"
    .. author_line
    .. "\n"

  return pandoc.RawBlock("latex", latex)

end