def svg_reservoir_parametric(wells, block_height=60, block_width=700,
                             margin_left=80, margin_top=30,
                             margin_pozo=20,
                             show_blocks=True, show_labels=True):
    """
    Genera un SVG conceptual con pozos paralelos y fracturas equiespaciadas.
    
    wells: lista de dicts
        [{'name': str, 'n_frac': int, 'color': str}, ...]
    block_height: altura fija de cada bloque (px) en modo conceptual
    block_width: ancho horizontal del reservorio (px)
    margin_left: margen izquierdo (px)
    margin_top: margen superior (px)
    margin_pozo: margen a los costados del pozo (px)
    show_blocks: si True, dibuja bloques O/I
    show_labels: si True, muestra etiquetas O/I
    """
    n_blocks = 2*len(wells) + 1
    total_height = block_height * n_blocks
    
    svg = [f"<svg xmlns='http://www.w3.org/2000/svg' "
           f"width='{block_width+250}' height='{total_height+2*margin_top}'>"]
    
    # marco externo
    svg.append(f"<rect x='{margin_left}' y='{margin_top}' "
               f"width='{block_width}' height='{total_height}' "
               f"fill='none' stroke='black' stroke-width='2'/>")
    
    y = margin_top
    for i, well in enumerate(wells, start=1):
        # Bloque O
        if show_blocks:
            svg.append(f"<rect x='{margin_left}' y='{y}' width='{block_width}' "
                       f"height='{block_height}' fill='#eeeeee' opacity='0.6' stroke='black'/>")
            if show_labels:
                svg.append(f"<text x='{margin_left+5}' y='{y+20}' font-size='13'>O{i}</text>")
        y += block_height
        
        # Bloque I con pozo
        if show_blocks:
            svg.append(f"<rect x='{margin_left}' y='{y}' width='{block_width}' "
                       f"height='{block_height}' fill='#cce6ff' opacity='0.5' stroke='black'/>")
            if show_labels:
                svg.append(f"<text x='{margin_left+5}' y='{y+20}' font-size='13'>I{i}</text>")
        
        pozo_y = y + block_height/2
        x1 = margin_left + margin_pozo
        x2 = margin_left + block_width - margin_pozo
        
        # línea del pozo
        svg.append(f"<line x1='{x1}' y1='{pozo_y}' x2='{x2}' y2='{pozo_y}' "
                   f"stroke='{well['color']}' stroke-width='2'/>")
        
        # fracturas equiespaciadas
        nfrac = well["n_frac"]
        if nfrac > 1:
            step = (x2 - x1)/(nfrac-1)
            for f in range(nfrac):
                xf = x1 + f*step
                svg.append(f"<line x1='{xf}' y1='{pozo_y-10}' x2='{xf}' y2='{pozo_y+10}' "
                           f"stroke='{well['color']}' stroke-width='2'/>")
        
        # etiqueta pozo
        svg.append(f"<text x='{margin_left+block_width+10}' y='{pozo_y+5}' "
                   f"font-size='12' fill='{well['color']}'>"
                   f"{well['name']} ({nfrac} fracturas)</text>")
        
        y += block_height
    
    # Bloque O final
    if show_blocks:
        svg.append(f"<rect x='{margin_left}' y='{y}' width='{block_width}' "
                   f"height='{block_height}' fill='#eeeeee' opacity='0.6' stroke='black'/>")
        if show_labels:
            svg.append(f"<text x='{margin_left+5}' y='{y+20}' font-size='13'>O{len(wells)+1}</text>")
    
    svg.append("</svg>")
    return "\n".join(svg)

def svg_reservoir_scaled(wells, xe, total_px=600,
                         block_width=700, margin_left=80, margin_top=30,
                         margin_pozo=20, show_blocks=True, show_labels=True):
    """
    Genera un SVG con bloques O/I a escala según spacing_g y 2xe.

    wells: [{'name': str, 'n_frac': int, 'color': str, 'spacing': float}, ...]
    xe: ancho 2xe (ft)
    total_px: altura total en píxeles del SVG
    """
    # lista de alturas físicas (ft)
    heights_ft, labels, types = [], [], []

    # O1
    heights_ft.append(xe); labels.append("O1"); types.append("O")

    for i, w in enumerate(wells, start=1):
        heights_ft.append(w["spacing"]); labels.append(f"I{i}"); types.append("I")
        heights_ft.append(xe); labels.append(f"O{i+1}"); types.append("O")

    total_ft = sum(heights_ft)
    scale = total_px / total_ft
    heights_px = [h*scale for h in heights_ft]

    total_height = sum(heights_px)
    svg = [f"<svg xmlns='http://www.w3.org/2000/svg' "
           f"width='{block_width+250}' height='{total_height+2*margin_top}'>"]

    # marco
    svg.append(f"<rect x='{margin_left}' y='{margin_top}' width='{block_width}' "
               f"height='{total_height}' fill='none' stroke='black' stroke-width='2'/>")

    y = margin_top
    well_index = 0
    for blk_h, lbl, typ in zip(heights_px, labels, types):
        color_fill = "#eeeeee" if typ=="O" else "#cce6ff"
        svg.append(f"<rect x='{margin_left}' y='{y}' width='{block_width}' "
                   f"height='{blk_h}' fill='{color_fill}' opacity='0.5' stroke='black'/>")
        if show_labels:
            svg.append(f"<text x='{margin_left+5}' y='{y+15}' font-size='12'>{lbl}</text>")

        if typ == "I":
            well = wells[well_index]
            pozo_y = y + blk_h/2
            x1 = margin_left + margin_pozo
            x2 = margin_left + block_width - margin_pozo

            # línea del pozo
            svg.append(f"<line x1='{x1}' y1='{pozo_y}' x2='{x2}' y2='{pozo_y}' "
                       f"stroke='{well['color']}' stroke-width='2'/>")

            # fracturas equiespaciadas
            nfrac = well["n_frac"]
            if nfrac > 1:
                step = (x2 - x1)/(nfrac-1)
                for f in range(nfrac):
                    xf = x1 + f*step
                    svg.append(f"<line x1='{xf}' y1='{pozo_y-10}' x2='{xf}' y2='{pozo_y+10}' "
                               f"stroke='{well['color']}' stroke-width='2'/>")

            # etiqueta pozo
            svg.append(f"<text x='{margin_left+block_width+10}' y='{pozo_y+5}' "
                       f"font-size='12' fill='{well['color']}'>"
                       f"{well['name']} ({nfrac} fracturas)</text>")

            well_index += 1
        y += blk_h

    svg.append("</svg>")
    return "\n".join(svg)
