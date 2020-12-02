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

function dictToTooltip(dict: object): string {
    let tooltip = ""
    for (let [param_name, param_val] of Object.entries(dict)) {
        tooltip += param_name + ": " + param_val + "<br>"
    }

    return tooltip
}

function init(graphData: GraphData) {
    monaco.editor.create(document.getElementById("start-editor"), {
        automaticLayout: true,
        language: "yaml"
    })

    monaco.editor.create(document.getElementById("target-editor"), {
        automaticLayout: true,
        language: "yaml"
    })

    // create a network
    let container = document.getElementById('solution-graph')

    // create an array with nodes
    let nodes: vis.Node[] = []

    // create an array with edges
    let edges: vis.Edge[] = []

    let nr_start_nodes = graphData.objects.filter(it => it.is_start).length
    let nr_end_nodes = graphData.objects.filter(it => !it.is_start && it.is_end).length

    let start_i = 0
    let end_i = 0

    let H_SPACE = 1000
    let V_SPACE = 300

    for (let ao of graphData.objects) {
        let newNode: vis.Node = {
            id: ao.id,
            label: "     " + ao.name + "     ",
            title: '<b>' + ao.type + '</b><br>' + dictToTooltip(ao.params),
            shape: "ellipse"
        }

        if (ao.is_start) {
            newNode.color = {
                border: '#b6be77',
                background: '#f4ff9e'
            }
            newNode.fixed = true
            newNode.x = (start_i - (nr_start_nodes - 1)/2)*H_SPACE
            start_i++
            newNode.y = 0
        } else if (ao.is_end) {
            newNode.color = {
                border: '#42cb52',
                background: '#bef7c5'
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
                    border: '#b86c6c',
                    background: '#fc9393'
                }
            }
        }

        nodes.push(newNode)
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

        nodes.push(methodNode)

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

            nodes.push(portNode)

            edges.push({
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
                nodes.push(demux)
                graphData.nextId++

                edges.push({
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

                nodes.push(portNode)

                edges.push({
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
        edges.push(newEdge)
    }

    let data = {
        nodes: nodes,
        edges: edges
    }
    let options: vis.Options = {
        physics: {
            barnesHut: {
                avoidOverlap: 0.1, // default 0
                springConstant: 0.2,  // default 0.04
                springLength: 40 // default 95
            },
            wind: {
                x: 0,
                y: 0
            }

        },
        autoResize: true,
        height: "100%"
    }
    network = new vis.Network(container, data, options)
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
(<any>window).stopPhysics = stopPhysics;
(<any>window).startPhysics = startPhysics;
