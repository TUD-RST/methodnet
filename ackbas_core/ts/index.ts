import * as vis from "vis-network/standalone";

interface GraphData {
    methods: {
        id: number
        name: string
        description: string
    }[]
    concreteTypes: {
        id: number
        name: string
        description: string
    }[]
    abstractTypes: {
        id: number
        name: string
        description: string
    }[]
    edges: {
        id: number
        fromId: number
        toId: number
    }[]
}

let network: vis.Network

function initGraph(graphData: GraphData) {
    // create an array with nodes
    let nodes: vis.Node[] = []

    for (let type of graphData.concreteTypes) {
        let newNode: vis.Node = {
            id: type.id,
            label: "     " + type.name + "     ",
            title: type.description.length ? type.description : undefined,
            shape: "ellipse",
            color: {
                border: '#42cb52',
                background: '#bef7c5'
            }
        }
        nodes.push(newNode)
    }
    for (let type of graphData.abstractTypes) {
        let newNode: vis.Node = {
            id: type.id,
            label: "     " + type.name + "     ",
            title: type.description.length ? type.description : undefined,
            shape: "ellipse",
            color: {
                border: '#c8db4c',
                background: '#e8ffa2'
            }
        }
        nodes.push(newNode)
    }

    for (let method of graphData.methods) {
        let newNode: vis.Node = {
            id: method.id,
            label: method.name,
            title: method.description.length ? method.description : undefined,
            shape: "box",
            color: {
                background: '#e6f0ff'
            }
        }
        nodes.push(newNode)
    }

    // create an array with edges
    let edges: vis.Edge[] = []

    for (let edge of graphData.edges) {
        let newEdge: vis.Edge = {
            //id: edge.id,
            from: edge.fromId,
            to: edge.toId,
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
