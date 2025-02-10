# TODO
# 4. handle comment environment
# 5. delete newif and longrue longfalse
# 7. add command line argument to delete comments


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


def reduce_comment(line):
    # TODO: possible problem: '\\\\%' break line before comment
    comment = re.match(r'(?<!\\)%.*', line)
    if comment:
        pos = comment.start()
        comment = line[pos:]
        line = line[:pos]
    else:
        comment = ''
    return line, comment

def process_latex_file(input_filename, output_filename, conditions):
    # Stack to keep track of \ifword conditions
    ignore_count = 0  # Counter to track nested \if{condition}

    defined_ifs = set()

    # Regular expressions
    newif_pattern = re.compile(r'\\newif\\if(\w+)')



    with open(input_filename, 'r', encoding='utf-8') as infile, open(output_filename, 'w', encoding='utf-8') as outfile:
        stack = []

        for line in infile:
            if ignore_count == 0 and len(line.strip()) == 0:
                outfile.write(line)
                continue
            line, comment = reduce_comment(line)

            newif_match = newif_pattern.search(line)
            if newif_match:
                defined_ifs.add(newif_match.group(1))                
                if ignore_count == 0:
                    outfile.write(line+comment)
                continue
            
            out=''
            # get all matches of if{condition}, else, fi using matchall
            all_matches = re.finditer(r'\\if(\w+)|\\else|\\fi', line)
            curr_match = next(all_matches, None)
            start_pos = 0

            def get_current_condition(match, stack_top_condition):
                if match.group(0).startswith('\\if'):
                    return [match.group(1), 'if']
                elif match.group(0) in ['\\else', '\\fi']:
                    return [stack_top_condition, match.group(0)[1:]]
                raise ValueError("Invalid match", match.group(0))
                return None
                

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
                # print rest and comment
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

    args = parser.parse_args()

    input_filename = args.input
    output_filename = args.output
    conditions = [(cond.split(':')[0], cond.split(':')[1].lower() == 'true') for cond in args.conditions.split(',')]

    process_latex_file(input_filename, output_filename, conditions)


if __name__ == '__main__':
    main()