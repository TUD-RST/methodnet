import * as vis from "vis-network/standalone";
import "bootstrap";
import "bootstrap/dist/css/bootstrap.min.css";
import * as monaco from "monaco-editor"

interface Port {
    id: number
    name: string
    constraints: object
    tune?: boolean
}

interface GraphData {
    methods: {
        id: number
        name: string
        inputs: Port[]
        outputs: Port[][]
        description: string | null
    }[]
    objects: {
        id: number
        type: string
        name: string
        is_start: boolean
        is_end: boolean
        distance_to_start: number
        on_solution_path: boolean
        params: object
    }[]
    connections: {
        fromId: number
        toId: number
    }[]
    nextId: number
}

let network: vis.Network
let networkData: {
    nodes: vis.DataSetNodes,
    edges: vis.DataSetEdges
}
let startEditor: monaco.editor.IStandaloneCodeEditor
let targetEditor: monaco.editor.IStandaloneCodeEditor

function dictToTooltip(dict: object): string {
    let tooltip = ""
    for (let [param_name, param_val] of Object.entries(dict)) {
        tooltip += param_name + ": " + param_val + "<br>"
    }

    return tooltip
}

function init() {
    startEditor = monaco.editor.create(document.getElementById("start-editor"), {
        automaticLayout: true,
        minimap: {
            enabled: false
        },
        language: "yaml",
        value:
`start:
  type: DGL
  params:
    Linear: NichtLinear
`
    })

    targetEditor = monaco.editor.create(document.getElementById("target-editor"), {
        automaticLayout: true,
        minimap: {
            enabled: false
        },
        language: "yaml",
        value:
`target:
  type: Trajektorienfolgeregler
`
    })

    // create a network
    let container = document.getElementById('solution-graph')

    networkData = {
        nodes: new vis.DataSet([]) as vis.DataSetNodes,
        edges: new vis.DataSet([]) as vis.DataSetEdges
    }
    let options: vis.Options = {
        physics: {
            barnesHut: {
                avoidOverlap: 0.1, // default 0
                springConstant: 0.2,  // default 0.04
                springLength: 20 // default 95
            },
            wind: {
                x: 0,
                y: 0
            }
        },
        autoResize: true,
        height: "100%"
    }

    network = new vis.Network(container, networkData, options)
}

async function update() {
    let path_components = window.location.pathname.split('/')
    let graphName = path_components[2]
    let startYML = startEditor.getValue()
    let targetYML = targetEditor.getValue()

    // TODO: Make URL relative
    let url = new URL('http://127.0.0.1:8000/s')
    let response = await fetch(url as any, {
        method: "POST",
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            "graph_name": graphName,
            "start": startYML,
            "target": targetYML
        })
    })

    let graphData = await response.json() as GraphData

    setNetworkData(graphData)
}

function setNetworkData(graphData: GraphData) {
    let nodes = networkData.nodes
    let edges = networkData.edges

    edges.clear()
    nodes.clear()

    let nr_start_nodes = graphData.objects.filter(it => it.is_start).length
    let nr_end_nodes = graphData.objects.filter(it => !it.is_start && it.is_end).length

    let start_i = 0
    let end_i = 0

    let H_SPACE = 1000
    let V_SPACE = 350

    for (let ao of graphData.objects) {
        let newNode: vis.Node = {
            id: ao.id,
            label: "     " + ao.name + "     ",
            title: '<b>' + ao.type + '</b><br>' + dictToTooltip(ao.params),
            shape: "ellipse"
        }

        if (ao.is_start) {
            newNode.color = {
                border: '#754fa7',
                background: '#b37aff'
            }
            newNode.fixed = true
            newNode.x = (start_i - (nr_start_nodes - 1)/2)*H_SPACE
            start_i++
            newNode.y = 0
        } else if (ao.is_end) {
            newNode.color = {
                border: '#42cb52',
                background: '#66db47'
            }
            newNode.fixed = true
            newNode.x = (end_i - (nr_end_nodes - 1)/2)*H_SPACE
            end_i++
            newNode.y = ao.distance_to_start*V_SPACE
        } else {
            if (ao.on_solution_path) {
                newNode.color = {
                    border: '#8bdde3',
                    background: '#9af9ff'
                }
            } else {
                newNode.color = {
                    border: '#b7b1b1',
                    background: '#e5d7d7'
                }
            }
        }

        nodes.add(newNode)
    }

    for (let method of graphData.methods) {
        let methodNode: vis.Node = {
            id: method.id,
            label: method.name,
            shape: "box",
            color: {
                background: '#e6f0ff'
            },
            title: method.description ?? undefined
        }

        nodes.add(methodNode)

        for (let port of method.inputs) {
            let portNode: vis.Node = {
                id: port.id,
                label: port.name,
                title: dictToTooltip(port.constraints),
                shape: "dot",
                size: 4,
                color: (port.tune ?? false) ? {
                    border: '#a770b3',
                    background: '#ed9eff'
                } : {
                    border: '#b6be77',
                    background: '#f4ff9e'
                }
            }

            nodes.add(portNode)

            edges.add({
                from: port.id,
                to: method.id,
                color: 'black',
                arrows: 'to'
            })
        }

        for (let output_option of method.outputs) {
            let demux_id

            if (method.outputs.length > 1) {
                let demux: vis.Node = {
                    id: graphData.nextId,
                    shape: "square",
                    color: {
                        background: "black",
                        border: "black"
                    },
                    size: 10
                }
                nodes.add(demux)
                graphData.nextId++

                edges.add({
                    from: method.id,
                    to: demux.id,
                    color: 'black',
                    arrows: 'to'
                })

                demux_id = demux.id
            } else {
                demux_id = method.id
            }

            for (let port of output_option) {
                let portNode: vis.Node = {
                    id: port.id,
                    label: port.name,
                    title: dictToTooltip(port.constraints),
                    shape: "dot",
                    size: 4,
                    color: {
                        border: '#42cb52',
                        background: '#bef7c5'
                    }
                }

                nodes.add(portNode)

                edges.add({
                    from: demux_id,
                    to: port.id,
                    color: 'black',
                    arrows: 'to'
                })
            }
        }
    }


    for (let con of graphData.connections) {
        let newEdge: vis.Edge = {
            //id: edge.id,
            from: con.fromId,
            to: con.toId,
            color: 'black',
            arrows: 'to'
        }
        edges.add(newEdge)
    }
}

function stopPhysics() {
    network.setOptions({
        physics: {
            enabled: false
        }
    })
}

function startPhysics() {
    network.setOptions({
        physics: {
            enabled: true
        }
    })
}

// make function globally available
// https://stackoverflow.com/questions/12709074/how-do-you-explicitly-set-a-new-property-on-window-in-typescript
(<any>window).init = init;
(<any>window).update = update;
(<any>window).stopPhysics = stopPhysics;
(<any>window).startPhysics = startPhysics;
