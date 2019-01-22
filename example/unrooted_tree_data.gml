graph [
  node [
    id 0
    label "CELL1"
  ]
  node [
    id 1
    label "CELL2"
  ]
  node [
    id 2
    label "CELL3"
  ]
  node [
    id 3
    label "CELL4"
  ]
  node [
    id 4
    label "LOCI1"
  ]
  node [
    id 5
    label "ROOT"
  ]
   edge [
   source 0
   target 5
  ]
  edge  [
   source 5
   target 3
  ]
  edge[
   source 4
   target 5
  ]
  edge [
   source 4
   target 1
  ]
  edge [
   source 4
   target 2
  ]
]
