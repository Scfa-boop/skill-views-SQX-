#!/usr/bin/env python3
"""Herramienta para crear y modificar vistas (.vw) del databank de StrategyQuant X.

Solo usa la biblioteca estándar. Conserva el formato del archivo original
(sangría, saltos de línea CRLF/LF, atributos en el mismo orden) para que la
vista nueva sea lo más parecida posible a la que SQX escribe por sí mismo.

Comandos:
  list    ARCHIVO                      muestra las columnas
  pair    ARCHIVO -o SALIDA            duplica cada KPI en versión (full) y (ISV1)
  add     ARCHIVO -o SALIDA ...        añade una columna
  remove  ARCHIVO -o SALIDA ...        quita columnas
  rename  ARCHIVO -o SALIDA ...        cambia el nombre de una columna

Códigos de salida: 0 = correcto, 1 = error de uso o de formato.
"""
import argparse
import re
import sys
import xml.etree.ElementTree as ET
from xml.sax.saxutils import quoteattr

# Columnas que no son una métrica por periodo: duplicarlas en ISV1 no aporta nada.
NO_DUPLICAR = {"EntryIndicators", "MiniEquityChart", "Symbol", "DateGenerated"}


def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def leer(path):
    """Devuelve (cabecera, columnas, estilo). columnas = lista de dicts ordenados."""
    try:
        raw = open(path, "rb").read()
    except OSError as e:
        fail(f"no se puede leer {path}: {e}")
    texto = raw.decode("utf-8-sig")
    crlf = "\r\n" in texto
    try:
        root = ET.fromstring(texto)
    except ET.ParseError as e:
        fail(f"{path} no es XML válido: {e}")
    if root.tag != "View":
        fail(f"el elemento raíz es <{root.tag}>, se esperaba <View>")
    hijos = list(root)
    if len(hijos) != 1 or hijos[0].tag != "Columns":
        fail("la vista tiene elementos distintos de <Columns>; formato no soportado. "
             "Pide al usuario un .vw de ejemplo y adapta la herramienta.")
    cols = []
    for c in hijos[0]:
        if c.tag != "Column" or len(c) or (c.text and c.text.strip()):
            fail("hay una <Column> con contenido interno o una etiqueta inesperada; "
                 "formato no soportado, no se reescribe para no perder datos.")
        cols.append(dict(c.attrib))
    m = re.search(r"\n( +)<Columns>", texto.replace("\r\n", "\n"))
    sangria = len(m.group(1)) if m else 2
    cabecera = dict(root.attrib)
    return cabecera, cols, {"crlf": crlf or "\n" not in texto, "sangria": sangria}


def escribir(path, cabecera, cols, estilo):
    nl = "\r\n" if estilo["crlf"] else "\n"
    s1 = " " * estilo["sangria"]
    s2 = s1 * 2
    attrs = " ".join(f"{k}={quoteattr(v)}" for k, v in cabecera.items())
    lineas = [f"<View {attrs}>", f"{s1}<Columns>"]
    for c in cols:
        a = " ".join(f"{k}={quoteattr(v)}" for k, v in c.items())
        lineas.append(f"{s2}<Column {a}/>")
    lineas += [f"{s1}</Columns>", "</View>"]
    data = nl.join(lineas) + nl
    with open(path, "wb") as f:
        f.write(data.encode("utf-8"))
    # Releer para comprobar que lo escrito es válido y tiene las columnas esperadas.
    _, de_nuevo, _ = leer(path)
    if len(de_nuevo) != len(cols):
        fail("la verificación posterior no coincide con lo escrito")


def quitar_sufijo(nombre):
    """Quita un sufijo (full) o (ISVn) ya existente, para que repetir el comando no duplique sufijos."""
    return re.sub(r"\s*\((?:full|ISV\d+)\)\s*$", "", nombre)


def cmd_list(a):
    _, cols, estilo = leer(a.archivo)
    print(f"{len(cols)} columnas  (saltos de línea: {'CRLF' if estilo['crlf'] else 'LF'})")
    for i, c in enumerate(cols):
        print(f"{i:>3}  {c.get('class', '?'):<22} sampleType={c.get('sampleType', '-'):<4} {c.get('name', '')}")


def cmd_pair(a):
    cab, cols, estilo = leer(a.archivo)
    excluir = NO_DUPLICAR | set(filter(None, (a.exclude or "").split(",")))
    solo = set(filter(None, (a.only or "").split(",")))
    nuevas, hechas, ya = [], [], []
    usadas = set()
    for i, c in enumerate(cols):
        if i in usadas:
            continue
        if c.get("sampleType") != a.base or c.get("class") in excluir or (solo and c.get("class") not in solo):
            nuevas.append(c)
            continue
        base = quitar_sufijo(c["name"])
        full = dict(c, name=f"{base} ({a.base_label})")
        nuevas.append(full)
        # ¿ya existe la gemela (misma clase y sampleType gemelo)? Se reutiliza en su sitio actual.
        gemela_idx = next((j for j, d in enumerate(cols)
                           if j != i and d.get("class") == c.get("class")
                           and d.get("sampleType") == a.twin and j not in usadas), None)
        if gemela_idx is not None:
            if gemela_idx > i:
                # Se coloca justo al lado de la base, para que queden juntas.
                usadas.add(gemela_idx)
            nuevas.append(dict(cols[gemela_idx], name=f"{base} ({a.twin_label})"))
            if gemela_idx < i:
                # la gemela ya se emitió antes de la base: se retira de esa posición
                for k in range(len(nuevas) - 2, -1, -1):
                    if nuevas[k].get("class") == c.get("class") and nuevas[k].get("sampleType") == a.twin:
                        del nuevas[k]
                        break
            ya.append(base)
        else:
            nuevas.append(dict(c, name=f"{base} ({a.twin_label})", sampleType=a.twin))
            hechas.append(base)
    # Columnas gemelas sueltas ya vistas en la lectura: se emiten tal cual si no se aparearon
    escribir(a.output, cab, nuevas, estilo)
    print(f"Escrito {a.output}: {len(cols)} -> {len(nuevas)} columnas")
    print(f"  pares creados ({len(hechas)}): {', '.join(hechas) or '-'}")
    print(f"  pares que ya existían y solo se renombraron ({len(ya)}): {', '.join(ya) or '-'}")


def cmd_add(a):
    cab, cols, estilo = leer(a.archivo)
    plantilla = dict(cols[0]) if cols else {}
    nueva = dict(plantilla)
    nueva.update({"class": a.klass, "name": a.name, "sampleType": a.sample_type})
    # Mantener el orden de atributos de la plantilla: class, name, sampleType primero.
    orden = list(plantilla.keys()) or list(nueva.keys())
    nueva = {k: nueva[k] for k in orden if k in nueva} | {k: v for k, v in nueva.items() if k not in orden}
    for par in a.set or []:
        k, _, v = par.partition("=")
        nueva[k] = v
    pos = len(cols)
    if a.after_class:
        idx = [i for i, c in enumerate(cols) if c.get("class") == a.after_class]
        if not idx:
            fail(f"no hay ninguna columna de clase {a.after_class}")
        pos = idx[-1] + 1
    cols.insert(pos, nueva)
    escribir(a.output, cab, cols, estilo)
    print(f"Añadida {a.klass} '{a.name}' (sampleType={a.sample_type}) en la posición {pos}. Total: {len(cols)}")


def _coincide(c, a):
    if a.klass and c.get("class") != a.klass:
        return False
    if a.sample_type and c.get("sampleType") != a.sample_type:
        return False
    if a.name and c.get("name") != a.name:
        return False
    return True


def cmd_remove(a):
    if not (a.klass or a.sample_type or a.name):
        fail("indica al menos --class, --sample-type o --name para no borrar todo por error")
    cab, cols, estilo = leer(a.archivo)
    quedan = [c for c in cols if not _coincide(c, a)]
    if len(quedan) == len(cols):
        fail("ninguna columna coincide con el filtro")
    escribir(a.output, cab, quedan, estilo)
    print(f"Quitadas {len(cols) - len(quedan)} columnas. Total: {len(quedan)}")


def cmd_rename(a):
    cab, cols, estilo = leer(a.archivo)
    n = 0
    for c in cols:
        if _coincide(c, a):
            c["name"] = a.new_name
            n += 1
    if not n:
        fail("ninguna columna coincide con el filtro")
    escribir(a.output, cab, cols, estilo)
    print(f"Renombradas {n} columnas a '{a.new_name}'")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)

    s = sp.add_parser("list"); s.add_argument("archivo"); s.set_defaults(f=cmd_list)

    s = sp.add_parser("pair"); s.add_argument("archivo"); s.add_argument("-o", "--output", required=True)
    s.add_argument("--base", default="127", help="sampleType del periodo completo (por defecto 127)")
    s.add_argument("--twin", default="41", help="sampleType del segundo periodo (por defecto 41 = ISV1)")
    s.add_argument("--base-label", default="full"); s.add_argument("--twin-label", default="ISV1")
    s.add_argument("--exclude", help="clases extra a no duplicar, separadas por coma")
    s.add_argument("--only", help="duplicar solo estas clases, separadas por coma")
    s.set_defaults(f=cmd_pair)

    s = sp.add_parser("add"); s.add_argument("archivo"); s.add_argument("-o", "--output", required=True)
    s.add_argument("--class", dest="klass", required=True); s.add_argument("--name", required=True)
    s.add_argument("--sample-type", required=True)
    s.add_argument("--after-class", help="insertar tras la última columna de esta clase")
    s.add_argument("--set", action="append", help="otro atributo, formato clave=valor (repetible)")
    s.set_defaults(f=cmd_add)

    s = sp.add_parser("remove"); s.add_argument("archivo"); s.add_argument("-o", "--output", required=True)
    s.add_argument("--class", dest="klass"); s.add_argument("--sample-type"); s.add_argument("--name")
    s.set_defaults(f=cmd_remove)

    s = sp.add_parser("rename"); s.add_argument("archivo"); s.add_argument("-o", "--output", required=True)
    s.add_argument("--class", dest="klass"); s.add_argument("--sample-type"); s.add_argument("--name")
    s.add_argument("--new-name", required=True)
    s.set_defaults(f=cmd_rename)

    a = p.parse_args()
    if getattr(a, "output", None) and a.output == a.archivo:
        fail("la salida no puede ser el mismo archivo que la entrada: conserva el original")
    a.f(a)


if __name__ == "__main__":
    main()
