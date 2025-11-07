"""
Spanish Transcript Word Frequency Analyzer

Analyzes word frequency in Spanish transcripts, excluding stop words (articles,
prepositions, conjunctions, pronouns, common verbs) to focus on semantic content
words (nouns, adjectives, domain-specific terms).

Excludes:
- Articles (el, la, los, las, un, una)
- Pronouns (yo, tú, me, te, se)
- Prepositions and contractions (de, del, en, con, por, para, al)
- Conjunctions (y, o, pero, porque)
- Common verbs (ser, estar, haber, tener, hacer, poder, ir, ver, dar, decir, etc.)
- Adverbs (muy, más, menos, ya, siempre)
- Numbers (cero through ciento)
- Discourse markers (además, entonces, sin embargo)

Usage:
    python analyze_transcript_words.py

Output:
    - Console: Top 100 most frequent content words
    - File: word_frequency_analysis.txt (top 200 words)
"""

import os
import re
from pathlib import Path
from collections import Counter
from typing import List, Dict

# Comprehensive Spanish stop words list
# Based on NLTK, Snowball, and linguistic research
SPANISH_STOP_WORDS = {
    # Articles
    'el', 'la', 'lo', 'los', 'las', 'un', 'una', 'unos', 'unas',

    # Pronouns
    'yo', 'tú', 'tu', 'él', 'ella', 'usted', 'nosotros', 'nosotras', 'vosotros',
    'vosotras', 'ellos', 'ellas', 'ustedes', 'me', 'te', 'se', 'nos', 'os', 'le',
    'les', 'lo', 'la', 'los', 'las', 'mi', 'mis', 'su', 'sus', 'nuestro', 'nuestra',
    'nuestros', 'nuestras', 'vuestro', 'vuestra', 'vuestros', 'vuestras',
    'mí', 'ti', 'sí', 'este', 'esta', 'esto', 'estos', 'estas', 'ese', 'esa',
    'eso', 'esos', 'esas', 'aquel', 'aquella', 'aquello', 'aquellos', 'aquellas',
    'quien', 'quienes', 'cual', 'cuales', 'que', 'qué',

    # Prepositions and contractions
    'a', 'ante', 'bajo', 'con', 'contra', 'de', 'del', 'desde', 'durante', 'en', 'entre',
    'hacia', 'hasta', 'mediante', 'para', 'por', 'según', 'sin', 'sobre', 'tras',
    'al',

    # Conjunctions
    'y', 'e', 'o', 'u', 'pero', 'mas', 'sino', 'aunque', 'si', 'porque', 'pues',
    'como', 'cuando', 'donde', 'mientras', 'ya', 'ni', 'entonces',

    # Connectors and discourse markers
    'además', 'también', 'tampoco', 'incluso', 'asimismo', 'luego', 'después',
    'antes', 'primero', 'segundo', 'finalmente', 'así', 'pues', 'entonces',
    'sin embargo', 'no obstante', 'por tanto', 'por lo tanto', 'es decir',
    'o sea', 'esto es', 'por ejemplo', 'además',

    # Auxiliary and common verbs (conjugated forms)
    'ser', 'es', 'soy', 'eres', 'son', 'somos', 'sois', 'era', 'eras', 'éramos',
    'eran', 'fui', 'fue', 'fuimos', 'fueron', 'sea', 'seas', 'seamos', 'sean',
    'sido', 'siendo',

    'estar', 'estoy', 'estás', 'está', 'estamos', 'estáis', 'están', 'estaba',
    'estabas', 'estábamos', 'estaban', 'estuve', 'estuvo', 'estuvimos', 'estuvieron',
    'esté', 'estés', 'estemos', 'estén', 'estado', 'estando',

    'haber', 'he', 'has', 'ha', 'hemos', 'habéis', 'han', 'había', 'habías',
    'habíamos', 'habían', 'hube', 'hubo', 'hubimos', 'hubieron', 'haya', 'hayas',
    'hayamos', 'hayan', 'habido', 'habiendo',

    'tener', 'tengo', 'tienes', 'tiene', 'tenemos', 'tenéis', 'tienen', 'tenía',
    'tenías', 'teníamos', 'tenían', 'tuve', 'tuvo', 'tuvimos', 'tuvieron', 'tenga',
    'tengas', 'tengamos', 'tengan', 'tenido', 'teniendo',

    'hacer', 'hago', 'haces', 'hace', 'hacemos', 'hacéis', 'hacen', 'hacía',
    'hacías', 'hacíamos', 'hacían', 'hice', 'hizo', 'hicimos', 'hicieron', 'haga',
    'hagas', 'hagamos', 'hagan', 'hecho', 'haciendo',

    'poder', 'puedo', 'puedes', 'puede', 'podemos', 'podéis', 'pueden', 'podía',
    'podías', 'podíamos', 'podían', 'pude', 'pudo', 'pudimos', 'pudieron', 'pueda',
    'puedas', 'podamos', 'puedan', 'podido', 'pudiendo',

    'ir', 'voy', 'vas', 'va', 'vamos', 'vais', 'van', 'iba', 'ibas', 'íbamos',
    'iban', 'fui', 'fue', 'fuimos', 'fueron', 'vaya', 'vayas', 'vayamos', 'vayan',
    'ido', 'yendo',

    'ver', 'veo', 'ves', 've', 'vemos', 'veis', 'ven', 'veía', 'veías', 'veíamos',
    'veían', 'vi', 'vio', 'vimos', 'vieron', 'vea', 'veas', 'veamos', 'vean',
    'visto', 'viendo',

    'dar', 'doy', 'das', 'da', 'damos', 'dais', 'dan', 'daba', 'dabas', 'dábamos',
    'daban', 'di', 'dio', 'dimos', 'dieron', 'dé', 'des', 'demos', 'den', 'dado',
    'dando',

    'decir', 'digo', 'dices', 'dice', 'decimos', 'decís', 'dicen', 'decía', 'decías',
    'decíamos', 'decían', 'dije', 'dijo', 'dijimos', 'dijeron', 'diga', 'digas',
    'digamos', 'digan', 'dicho', 'diciendo',

    # Common verbs (additional)
    'saber', 'sé', 'sabes', 'sabe', 'sabemos', 'sabéis', 'saben', 'sabía', 'sabías',
    'sabíamos', 'sabían', 'supe', 'supo', 'supimos', 'supieron', 'sepa', 'sepas',
    'sepamos', 'sepan', 'sabido', 'sabiendo',

    'querer', 'quiero', 'quieres', 'quiere', 'queremos', 'queréis', 'quieren', 'quería',
    'querías', 'queríamos', 'querían', 'quise', 'quiso', 'quisimos', 'quisieron', 'quiera',
    'quieras', 'queramos', 'quieran', 'querido', 'queriendo',

    'llegar', 'llego', 'llegas', 'llega', 'llegamos', 'llegáis', 'llegan', 'llegaba',
    'llegabas', 'llegábamos', 'llegaban', 'llegué', 'llegó', 'llegamos', 'llegaron',
    'llegue', 'llegues', 'lleguemos', 'lleguen', 'llegado', 'llegando',

    'pasar', 'paso', 'pasas', 'pasa', 'pasamos', 'pasáis', 'pasan', 'pasaba', 'pasabas',
    'pasábamos', 'pasaban', 'pasé', 'pasó', 'pasamos', 'pasaron', 'pase', 'pases',
    'pasemos', 'pasen', 'pasado', 'pasando',

    'poner', 'pongo', 'pones', 'pone', 'ponemos', 'ponéis', 'ponen', 'ponía', 'ponías',
    'poníamos', 'ponían', 'puse', 'puso', 'pusimos', 'pusieron', 'ponga', 'pongas',
    'pongamos', 'pongan', 'puesto', 'poniendo',

    'llevar', 'llevo', 'llevas', 'lleva', 'llevamos', 'lleváis', 'llevan', 'llevaba',
    'llevabas', 'llevábamos', 'llevaban', 'llevé', 'llevó', 'llevamos', 'llevaron',
    'lleve', 'lleves', 'llevemos', 'lleven', 'llevado', 'llevando',

    'venir', 'vengo', 'vienes', 'viene', 'venimos', 'venís', 'vienen', 'venía', 'venías',
    'veníamos', 'venían', 'vine', 'vino', 'vinimos', 'vinieron', 'venga', 'vengas',
    'vengamos', 'vengan', 'venido', 'viniendo',

    'salir', 'salgo', 'sales', 'sale', 'salimos', 'salís', 'salen', 'salía', 'salías',
    'salíamos', 'salían', 'salí', 'salió', 'salimos', 'salieron', 'salga', 'salgas',
    'salgamos', 'salgan', 'salido', 'saliendo',

    'seguir', 'sigo', 'sigues', 'sigue', 'seguimos', 'seguís', 'siguen', 'seguía',
    'seguías', 'seguíamos', 'seguían', 'seguí', 'siguió', 'seguimos', 'siguieron',
    'siga', 'sigas', 'sigamos', 'sigan', 'seguido', 'siguiendo',

    'creer', 'creo', 'crees', 'cree', 'creemos', 'creéis', 'creen', 'creía', 'creías',
    'creíamos', 'creían', 'creí', 'creyó', 'creímos', 'creyeron', 'crea', 'creas',
    'creamos', 'crean', 'creído', 'creyendo',

    'pensar', 'pienso', 'piensas', 'piensa', 'pensamos', 'pensáis', 'piensan', 'pensaba',
    'pensabas', 'pensábamos', 'pensaban', 'pensé', 'pensó', 'pensamos', 'pensaron',
    'piense', 'pienses', 'pensemos', 'piensen', 'pensado', 'pensando',

    'encontrar', 'encuentro', 'encuentras', 'encuentra', 'encontramos', 'encontráis',
    'encuentran', 'encontraba', 'encontrabas', 'encontrábamos', 'encontraban', 'encontré',
    'encontró', 'encontramos', 'encontraron', 'encuentre', 'encuentres', 'encontremos',
    'encuentren', 'encontrado', 'encontrando',

    'parecer', 'parezco', 'pareces', 'parece', 'parecemos', 'parecéis', 'parecen',
    'parecía', 'parecías', 'parecíamos', 'parecían', 'parecí', 'pareció', 'parecimos',
    'parecieron', 'parezca', 'parezcas', 'parezcamos', 'parezcan', 'parecido', 'pareciendo',

    'quedar', 'quedo', 'quedas', 'queda', 'quedamos', 'quedáis', 'quedan', 'quedaba',
    'quedabas', 'quedábamos', 'quedaban', 'quedé', 'quedó', 'quedamos', 'quedaron',
    'quede', 'quedes', 'quedemos', 'queden', 'quedado', 'quedando',

    'dejar', 'dejo', 'dejas', 'deja', 'dejamos', 'dejáis', 'dejan', 'dejaba', 'dejabas',
    'dejábamos', 'dejaban', 'dejé', 'dejó', 'dejamos', 'dejaron', 'deje', 'dejes',
    'dejemos', 'dejen', 'dejado', 'dejando',

    'sentir', 'siento', 'sientes', 'siente', 'sentimos', 'sentís', 'sienten', 'sentía',
    'sentías', 'sentíamos', 'sentían', 'sentí', 'sintió', 'sentimos', 'sintieron',
    'sienta', 'sientas', 'sintamos', 'sientan', 'sentido', 'sintiendo',

    'hablar', 'hablo', 'hablas', 'habla', 'hablamos', 'habláis', 'hablan', 'hablaba',
    'hablabas', 'hablábamos', 'hablaban', 'hablé', 'habló', 'hablamos', 'hablaron',
    'hable', 'hables', 'hablemos', 'hablen', 'hablado', 'hablando',

    'tratar', 'trato', 'tratas', 'trata', 'tratamos', 'tratáis', 'tratan', 'trataba',
    'tratabas', 'tratábamos', 'trataban', 'traté', 'trató', 'tratamos', 'trataron',
    'trate', 'trates', 'tratemos', 'traten', 'tratado', 'tratando',

    'trabajar', 'trabajo', 'trabajas', 'trabaja', 'trabajamos', 'trabajáis', 'trabajan',
    'trabajaba', 'trabajabas', 'trabajábamos', 'trabajaban', 'trabajé', 'trabajó',
    'trabajamos', 'trabajaron', 'trabaje', 'trabajes', 'trabajemos', 'trabajen',
    'trabajado', 'trabajando',

    'presentar', 'presento', 'presentas', 'presenta', 'presentamos', 'presentáis',
    'presentan', 'presentaba', 'presentabas', 'presentábamos', 'presentaban', 'presenté',
    'presentó', 'presentamos', 'presentaron', 'presente', 'presentes', 'presentemos',
    'presenten', 'presentado', 'presentando',

    'considerar', 'considero', 'consideras', 'considera', 'consideramos', 'consideráis',
    'consideran', 'consideraba', 'considerabas', 'considerábamos', 'consideraban',
    'consideré', 'consideró', 'consideramos', 'consideraron', 'considere', 'consideres',
    'consideremos', 'consideren', 'considerado', 'considerando',

    'realizar', 'realizo', 'realizas', 'realiza', 'realizamos', 'realizáis', 'realizan',
    'realizaba', 'realizabas', 'realizábamos', 'realizaban', 'realicé', 'realizó',
    'realizamos', 'realizaron', 'realice', 'realices', 'realicemos', 'realicen',
    'realizado', 'realizando',

    'producir', 'produzco', 'produces', 'produce', 'producimos', 'producís', 'producen',
    'producía', 'producías', 'producíamos', 'producían', 'produje', 'produjo', 'produjimos',
    'produjeron', 'produzca', 'produzcas', 'produzcamos', 'produzcan', 'producido',
    'produciendo',

    'entrar', 'entro', 'entras', 'entra', 'entramos', 'entráis', 'entran', 'entraba',
    'entrabas', 'entrábamos', 'entraban', 'entré', 'entró', 'entramos', 'entraron',
    'entre', 'entres', 'entremos', 'entren', 'entrado', 'entrando',

    'formar', 'formo', 'formas', 'forma', 'formamos', 'formáis', 'forman', 'formaba',
    'formabas', 'formábamos', 'formaban', 'formé', 'formó', 'formamos', 'formaron',
    'forme', 'formes', 'formemos', 'formen', 'formado', 'formando',

    'empezar', 'empiezo', 'empiezas', 'empieza', 'empezamos', 'empezáis', 'empiezan',
    'empezaba', 'empezabas', 'empezábamos', 'empezaban', 'empecé', 'empezó', 'empezamos',
    'empezaron', 'empiece', 'empieces', 'empecemos', 'empiecen', 'empezado', 'empezando',

    'obtener', 'obtengo', 'obtienes', 'obtiene', 'obtenemos', 'obtenéis', 'obtienen',
    'obtenía', 'obtenías', 'obteníamos', 'obtenían', 'obtuve', 'obtuvo', 'obtuvimos',
    'obtuvieron', 'obtenga', 'obtengas', 'obtengamos', 'obtengan', 'obtenido', 'obteniendo',

    'observar', 'observo', 'observas', 'observa', 'observamos', 'observáis', 'observan',
    'observaba', 'observabas', 'observábamos', 'observaban', 'observé', 'observó',
    'observamos', 'observaron', 'observe', 'observes', 'observemos', 'observen',
    'observado', 'observando',

    'recordar', 'recuerdo', 'recuerdas', 'recuerda', 'recordamos', 'recordáis', 'recuerdan',
    'recordaba', 'recordabas', 'recordábamos', 'recordaban', 'recordé', 'recordó',
    'recordamos', 'recordaron', 'recuerde', 'recuerdes', 'recordemos', 'recuerden',
    'recordado', 'recordando',

    'deber', 'debo', 'debes', 'debe', 'debemos', 'debéis', 'deben', 'debía', 'debías',
    'debíamos', 'debían', 'debí', 'debió', 'debimos', 'debieron', 'deba', 'debas',
    'debamos', 'deban', 'debido', 'debiendo',

    'permitir', 'permito', 'permites', 'permite', 'permitimos', 'permitís', 'permiten',
    'permitía', 'permitías', 'permitíamos', 'permitían', 'permití', 'permitió',
    'permitimos', 'permitieron', 'permita', 'permitas', 'permitamos', 'permitan',
    'permitido', 'permitiendo',

    # Adverbs (common non-content)
    'no', 'sí', 'muy', 'más', 'menos', 'poco', 'mucho', 'bastante', 'demasiado',
    'tan', 'tanto', 'cuanto', 'cómo', 'cuándo', 'dónde', 'ya', 'aún', 'todavía',
    'siempre', 'nunca', 'jamás', 'quizás', 'tal vez', 'acaso', 'bien', 'mal',
    'aquí', 'ahí', 'allí', 'allá', 'cerca', 'lejos', 'ahora', 'hoy', 'ayer',
    'mañana', 'tarde', 'temprano',

    # Question words
    'qué', 'quién', 'quiénes', 'cuál', 'cuáles', 'cómo', 'cuándo', 'dónde',
    'cuánto', 'cuánta', 'cuántos', 'cuántas', 'por qué',

    # Numbers 0-100
    'cero', 'uno', 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete', 'ocho',
    'nueve', 'diez', 'once', 'doce', 'trece', 'catorce', 'quince', 'dieciséis',
    'diecisiete', 'dieciocho', 'diecinueve', 'veinte', 'treinta', 'cuarenta',
    'cincuenta', 'sesenta', 'setenta', 'ochenta', 'noventa', 'cien', 'ciento',

    # Other common function words
    'mismo', 'misma', 'mismos', 'mismas', 'otro', 'otra', 'otros', 'otras',
    'todo', 'toda', 'todos', 'todas', 'alguno', 'alguna', 'algunos', 'algunas',
    'ninguno', 'ninguna', 'ningunos', 'ningunas', 'cada', 'ambos', 'ambas',
    'varios', 'varias', 'tal', 'tales', 'cualquier', 'cualquiera', 'cualesquiera',

    # Interjections and fillers
    'ah', 'oh', 'eh', 'ay', 'uy', 'bueno', 'pues', 'vale',

    # Other exclusions
    'música',
}


def read_transcript_file(filepath: Path) -> str:
    """
    Read transcript file and extract only the transcript text.

    Skips metadata header (lines before the separator line).

    Args:
        filepath: Path to transcript file

    Returns:
        Transcript text only
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Find the separator line (===)
        separator_idx = None
        for i, line in enumerate(lines):
            if '=' * 10 in line:  # At least 10 equal signs
                separator_idx = i
                break

        if separator_idx is None:
            # No separator found, assume entire file is transcript
            return ''.join(lines)

        # Return everything after the separator
        transcript_lines = lines[separator_idx + 1:]
        return ''.join(transcript_lines)

    except Exception as e:
        print(f"Error reading {filepath.name}: {e}")
        return ""


def normalize_text(text: str) -> str:
    """
    Normalize text for word counting.

    - Convert to lowercase
    - Remove punctuation except hyphens in compound words
    - Keep accented characters (á, é, í, ó, ú, ñ)

    Args:
        text: Input text

    Returns:
        Normalized text
    """
    # Convert to lowercase
    text = text.lower()

    # Remove punctuation but keep spaces and hyphens
    # Keep Spanish accented characters
    text = re.sub(r'[^\w\s\-áéíóúüñ]', ' ', text)

    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def extract_content_words(text: str, stop_words: set) -> List[str]:
    """
    Extract content words from text, filtering out stop words.

    Args:
        text: Normalized text
        stop_words: Set of words to exclude

    Returns:
        List of content words
    """
    words = text.split()

    # Filter out stop words and very short words (< 3 chars)
    content_words = [
        word for word in words
        if word not in stop_words and len(word) >= 3
    ]

    return content_words


def analyze_transcripts(transcript_dir: Path, stop_words: set) -> Counter:
    """
    Analyze all transcripts in directory and count word frequencies.

    Args:
        transcript_dir: Directory containing transcript files
        stop_words: Set of stop words to exclude

    Returns:
        Counter object with word frequencies
    """
    all_words = []
    transcript_files = list(transcript_dir.glob('*.txt'))

    print(f"Found {len(transcript_files)} transcript files")
    print("Processing...\n")

    for filepath in transcript_files:
        # Read and extract transcript text
        transcript_text = read_transcript_file(filepath)

        if not transcript_text:
            continue

        # Normalize text
        normalized = normalize_text(transcript_text)

        # Extract content words
        content_words = extract_content_words(normalized, stop_words)
        all_words.extend(content_words)

        print(f"  Processed: {filepath.name} ({len(content_words)} content words)")

    # Count frequencies
    word_counts = Counter(all_words)

    return word_counts


def save_results(word_counts: Counter, output_file: Path, top_n: int = 100):
    """
    Save word frequency results to file.

    Args:
        word_counts: Counter with word frequencies
        output_file: Path to output file
        top_n: Number of top words to save (default: 100)
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Spanish Transcript Word Frequency Analysis\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Total unique content words: {len(word_counts)}\n")
        f.write(f"Total word occurrences: {sum(word_counts.values())}\n\n")
        f.write(f"Top {top_n} Most Frequent Words:\n")
        f.write("-" * 70 + "\n")
        f.write(f"{'Rank':<6} {'Word':<25} {'Count':<10} {'Percentage':<10}\n")
        f.write("-" * 70 + "\n")

        total = sum(word_counts.values())
        for rank, (word, count) in enumerate(word_counts.most_common(top_n), 1):
            percentage = (count / total) * 100
            f.write(f"{rank:<6} {word:<25} {count:<10} {percentage:<10.2f}%\n")

    print(f"\nResults saved to: {output_file}")


def print_top_words(word_counts: Counter, top_n: int = 100):
    """
    Print top N words to console.

    Args:
        word_counts: Counter with word frequencies
        top_n: Number of words to display (default: 100)
    """
    print(f"\n{'='*70}")
    print(f"Top {top_n} Most Frequent Content Words")
    print(f"{'='*70}\n")
    print(f"{'Rank':<6} {'Word':<25} {'Count':<10} {'Percentage':<10}")
    print("-" * 70)

    total = sum(word_counts.values())
    for rank, (word, count) in enumerate(word_counts.most_common(top_n), 1):
        percentage = (count / total) * 100
        print(f"{rank:<6} {word:<25} {count:<10} {percentage:<10.2f}%")

    print(f"\nTotal unique content words: {len(word_counts):,}")
    print(f"Total word occurrences: {total:,}")


def main():
    """Main execution function."""
    # Setup paths (script is in scripts/, data is in parent directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    transcript_dir = project_root / 'backlog_JLC' / 'transcripts'
    output_file = project_root / 'word_frequency_analysis.txt'

    # Validate directory exists
    if not transcript_dir.exists():
        print(f"ERROR: Transcript directory not found: {transcript_dir}")
        return

    print("Spanish Transcript Word Frequency Analyzer")
    print("=" * 70)
    print(f"Transcript directory: {transcript_dir}")
    print(f"Stop words loaded: {len(SPANISH_STOP_WORDS)}\n")

    # Analyze transcripts
    word_counts = analyze_transcripts(transcript_dir, SPANISH_STOP_WORDS)

    if not word_counts:
        print("\nNo words found. Check transcript files.")
        return

    # Display results
    print_top_words(word_counts, top_n=100)

    # Save full results
    save_results(word_counts, output_file, top_n=200)

    print("\n" + "=" * 70)
    print("Analysis complete!")


if __name__ == "__main__":
    main()
