import * as vis from "vis-network/standalone";
import { Edge } from "vis-network/standalone";

interface GraphData {
    types: string[],
    methods: string[],
    flowEdges: [string, string][]
    deriveEdges: [string, string][]
}

interface NodeSpec {
    id: number
    label: string
    shape?: 'ellipse' | 'box'
    color?: {
        border: string
        background: string
    }
}

interface EdgeSpec {
    from: number
    to: number
    arrows: string
    dashes?: boolean
    color?: string
}

let network: vis.Network

function initGraph(graphData: GraphData) {
    let labelToId: Map<string, number> = new Map()

    // create an array with nodes
    let nodes: NodeSpec[] = []

    let id = 1

    for (let type of graphData.types) {
        let newNode: NodeSpec = {
            id: id,
            label: type,
            shape: "ellipse",
            color: {
                border: '#61ff74',
                background: '#bef7c5'
            }
        }
        nodes.push(newNode)
        labelToId.set(type, id)
        id++
    }

    for (let method of graphData.methods) {
        let newNode: NodeSpec = {
            id: id,
            label: method,
            shape: "box"
        }
        nodes.push(newNode)
        labelToId.set(method, id)
        id++
    }

    // create an array with edges
    let edges: EdgeSpec[] = []

    for (let labels of graphData.flowEdges) {
        let id1 = labelToId.get(labels[0])
        let id2 = labelToId.get(labels[1])

        let newEdge: EdgeSpec = {
            from: id1,
            to: id2,
            arrows: 'to',
            color: '#2B7CE9'
        }

        edges.push(newEdge)
    }

    for (let labels of graphData.deriveEdges) {
        let id1 = labelToId.get(labels[0])
        let id2 = labelToId.get(labels[1])

        let newEdge: EdgeSpec = {
            from: id1,
            to: id2,
            arrows: 'to',
            dashes: true,
            color: '#2B7CE9'
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
                springConstant: 0.02,  // default 0.04
                springLength: 150 // default 95
            }
        }
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
