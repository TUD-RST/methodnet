import * as vis from "vis-network/standalone";
import "bootstrap";
import "bootstrap/dist/css/bootstrap.min.css";

interface Port {
    id: number
    name: string
    constraints: object
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

function initGraph(graphData: GraphData) {
    // create an array with nodes
    let nodes: vis.Node[] = []

    // create an array with edges
    let edges: vis.Edge[] = []

    for (let ao of graphData.objects) {
        let color
        if (ao.is_start) {
            color = {
                border: '#b6be77',
                background: '#f4ff9e'
            }
        } else if (ao.is_end) {
            color = {
                border: '#42cb52',
                background: '#bef7c5'
            }
        } else {
            color = {
                border: '#8bdde3',
                background: '#9af9ff'
            }
        }

        let newNode: vis.Node = {
            id: ao.id,
            label: "     " + ao.name + "     ",
            title: '<b>' + ao.type + '</b><br>' + dictToTooltip(ao.params),
            shape: "ellipse",
            color: color
        }
        nodes.push(newNode)
    }

    // fix first object for physics
    nodes[0].fixed = true

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
                color: {
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

    // create a network
    let container = document.getElementById('mynetwork')
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
                y: 0.5
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
(<any>window).initGraph = initGraph;
(<any>window).stopPhysics = stopPhysics;
(<any>window).startPhysics = startPhysics;
