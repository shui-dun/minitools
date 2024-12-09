---
ctime: <% tp.date.now("YYYY-MM-DD") %>
tags: [<% tp.user.cursor(1) %>]
sr: [2.5,1.0,<% tp.date.now("YYYY-MM-DD", 1) %>]
---
# <% tp.file.title %>

<% tp.user.cursor(2) %>

# EOF
```meta-bind-embed
[note-eof](note-eof.md)
```
