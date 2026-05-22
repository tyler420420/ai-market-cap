# Test what different Python string values produce
test1 = '"\'+sortCol+\'"'
print('test1 value:', repr(test1))
# In HTML JS single-quoted: 'th[data-col="'+sortCol+'"]'
# This means: open JS string, add th[data-col=", add sortCol, add '"]'

# What Python string produces this?
# In Python: "'+sortCol+'" is the string value: '+sortCol+'
# We need the quotes around sortCol to ALSO be in the JS output

# So: '"\'+sortCol+\'"' as Python = "\"'+sortCol+'\""
# But this produces: "'+sortCol+'" which is wrong

# We need: "th[data-col=\"" + sortCol + "\"]"
# As Python: "th[data-col=\"\\'" + sortCol + "\\'\"]"

# Actually let's just look at what we want:
# In final HTML JS: querySelector('th[data-col="'+sortCol+'"]')
# Breaking it down for a Python double-quoted string:
# "querySelector('th[data-col=\"'+sortCol+'\"']')"
# That's: open dquote, querySelector('th[data-col=\", '+sortCol+', "\']'), close dquote

test = "querySelector('th[data-col=\"\\'+sortCol+'\\'\"]')"
print('test:', repr(test))
print('Display:', test)