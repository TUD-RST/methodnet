import * as vis from "vis-network/standalone";
import { Edge } from "vis-network/standalone";

interface GraphData {
    types: string[],
    methods: string[],
    flowEdges: [string, string][]
    deriveEdges: [string, string][]
}

class NodeSpec {
    id: number
    label: string
    shape: 'ellipse' | 'box'
}

class EdgeSpec {
    from: number
    to: number
    arrows: string
    dashes?: boolean
}

function initGraph(graphData: GraphData) {
    let labelToId: Map<string, number> = new Map()

    // create an array with nodes
    let nodes: NodeSpec[] = []

    let id = 1

    for (let type of graphData.types) {
        let newNode: NodeSpec = {
            id: id,
            label: type,
            shape: "ellipse"
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
            arrows: 'to'
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
            dashes: true
        }

        edges.push(newEdge)
    }

    // create a network
    let container = document.getElementById('mynetwork')
    let data = {
        nodes: nodes,
        edges: edges
    }
    let options = {}
    let network = new vis.Network(container, data, options)
}

// make function globally available
// https://stackoverflow.com/questions/12709074/how-do-you-explicitly-set-a-new-property-on-window-in-typescript
(<any>window).initGraph = initGraph