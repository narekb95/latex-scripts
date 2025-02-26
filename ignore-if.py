# TODO
# 4. handle comment environment
# 5. delete newif and longrue longfalse
# 7. add command line argument to delete comments

from os import path
import re
import argparse



def handle_output(line, curr_pos, match, matched_condition):
    out = ''
    command_pos = match.start() if match else None

    prefix = line[curr_pos:command_pos]
    out+=prefix

    if matched_condition is None:
            out+=match.group(0)

    return out

def find_comment_start(line: str) -> int:
    """
    Returns the index where the comment starts in a LaTeX line.
    If no unescaped % is found, returns -1.
    """
    for i, ch in enumerate(line):
        if ch == '%':
            # Count consecutive backslashes immediately before the %
            backslash_count = 0
            j = i - 1
            while j >= 0 and line[j] == '\\':
                backslash_count += 1
                j -= 1
            # If backslash_count is even, then % is not escaped
            if backslash_count % 2 == 0:
                return i
    return -1

def reduce_comment(line):
    start = find_comment_start(line)
    if start == -1:
        return line, ''
    return line[:start], line[start:]

def expand_input(input_filename, base_path):
    out_path = path.join(base_path, 'tmp.tex')

    input_pat = re.compile(r'\\input{(.+)}')
    text = None
    with open(input_filename, 'r', encoding='utf-8') as infile:
        text = infile.read()

    prefix = ''
    last_pos = 0
    for match in input_pat.finditer(text):
        input_file = match.group(1)
        if not input_file.endswith('.tex'):
            input_file += '.tex'
        input_file = path.join(base_path, input_file)
        prefix += text[last_pos:match.start()]
        with open(input_file, 'r', encoding='utf-8') as infile:
            prefix += infile.read()
        last_pos = match.end()
    prefix += text[last_pos:]
    with open(out_path, 'w', encoding='utf-8') as outfile:
        outfile.write(prefix)
    return out_path

        

# [TODO]: only expand if in output context, and recursively line by line directly to output (implement function process_line and call recursively on input)
def process_latex_file(input_path, output_filename, conditions, delete_comments, recursive):
    base_path = path.dirname(input_path)
    out_path = path.join(base_path, output_filename)
    if recursive:
        input_filename = expand_input(input_path, base_path)
    base_path = path.dirname(input_path)
    # Stack to keep track of \ifword conditions
    ignore_count = 0  # Counter to track nested \if{condition}

    defined_ifs = set()

    # Regular expressions
    newif_pattern = re.compile(r'\\newif\\if(\w+)')



    with open(input_filename, 'r', encoding='utf-8') as infile, open(out_path, 'w', encoding='utf-8') as outfile:
        stack = []

        for i, line in enumerate(infile):
            # If line is empty and ignore_count is 0, write it
            # Empty output will be ignored otherwise
            if ignore_count == 0 and len(line.strip()) == 0:
                outfile.write(line)
                continue
            line, comment = reduce_comment(line)
            if delete_comments and comment.endswith('\n'):
                comment = '\n'

            newif_match = newif_pattern.search(line)
            if newif_match:
                defined_ifs.add(newif_match.group(1))                
                if ignore_count == 0:
                    outfile.write(line+comment)
                continue
            
            out=''
            all_matches = re.finditer(r'\\if(\w+)|\\else|\\fi', line)
            curr_match = next(all_matches, None)
            start_pos = 0

            def get_current_condition(match, stack_top_condition):
                if match.group(0).startswith('\\if'):
                    return [match.group(1), 'if']
                elif match.group(0) in ['\\else', '\\fi']:
                    return [stack_top_condition, match.group(0)[1:]]
                raise ValueError("Invalid match", match.group(0))              

            while curr_match:
                curr_command = get_current_condition(curr_match, stack[-1][0] if len(stack) else None)
                matched_condition = next((condition for condition in conditions if condition[0] == curr_command[0]), None)
                ignore_condition = matched_condition[1] if matched_condition else False
                
                if ignore_count == 0:
                    out += handle_output(line, start_pos, curr_match, matched_condition)

                if curr_command[1] == 'if' and curr_command[0] in defined_ifs:
                    stack.append(curr_command)
                    if matched_condition and ignore_condition:
                            ignore_count += 1
                elif curr_command[1] == 'else':
                    stack[-1] = curr_command
                    if matched_condition:
                        if ignore_condition:
                            ignore_count -= 1
                        else:
                            ignore_count += 1
                elif curr_command[1] == 'fi':
                    state=stack[-1][1]
                    stack.pop()
                    if matched_condition:
                        if (state == 'if' and  ignore_condition)\
                            or (state == 'else' and not ignore_condition):
                            ignore_count -= 1

                start_pos = curr_match.end()
                curr_match = next(all_matches, None)

            if ignore_count == 0:
                out += line[start_pos:] + comment
            # if lien is empty now (wasn't empty before) don't write it
            # else might start paragraph
            if len(out.rstrip()) > 0:
                outfile.write(out)

def main():
    parser = argparse.ArgumentParser(description='Process a LaTeX file with conditional ignoring \\if{word}.')
    parser.add_argument('--input', required=True, help='Input LaTeX file')
    parser.add_argument('--output', required=True, help='Output LaTeX file')
    parser.add_argument('--conditions', required=True, help='Conditions to ignore in the format "condition1:true,condition2:false".\\Use true to remove the "if" branch, and false to remove the "else" branch.')
    parser.set_defaults(delete_comments=False)
    parser.add_argument('--delete-comments', action='store_true', help='Delete comments.')

    parser.add_argument('--recursive', action='store_true', help='Recursively expand input commands.')
    parser.set_defaults(recursive=False)

    args = parser.parse_args()

    input_filename = args.input
    output_filename = args.output
    conditions = [(cond.split(':')[0], cond.split(':')[1].lower() == 'true') for cond in args.conditions.split(',')]
    delete_comments = args.delete_comments
    recursive = args.recursive

    process_latex_file(input_filename, output_filename, conditions, delete_comments, recursive)


if __name__ == '__main__':
    main()