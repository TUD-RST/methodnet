import * as vis from "vis-network/standalone";
import {KnowledgeGraphData, SolutionGraphData} from "./methodnet_data";

let knowledgeGraphNetwork: vis.Network
let knowledgeGraphNetworkData: {
    nodes: vis.DataSetNodes,
    edges: vis.DataSetEdges
}

let solutionGraphNetwork: vis.Network
let solutionGraphNetworkData: {
    nodes: vis.DataSetNodes,
    edges: vis.DataSetEdges
}

let typeToId: Record<string, number> = {}  // Map from type name to knowledge graph node id
let methodToId: Record<string, number> = {}  // Map from method name to knowledge graph node id
let edgeIds: [string, string, number][] = []  // Map from knowledge graph connection (t -> m or m -> t) to edge id

/** Set up VisJS for knowledge graph */
export function initKnowledgeGraph(div: HTMLElement) {
    let knowledgeGraphOptions: vis.Options = {
        physics: {
            barnesHut: {
                avoidOverlap: 0.1, // default 0
                springConstant: 0.002,  // default 0.04
                springLength: 50, // default 95
                centralGravity: 0.1,
                gravitationalConstant: -3000
            }
        },
        autoResize: true,
        height: "100%"
    }

    let knowledgeGraphContainer = document.getElementById('knowledge-graph')
    knowledgeGraphNetworkData = {
        nodes: new vis.DataSet([]) as vis.DataSetNodes,
        edges: new vis.DataSet([]) as vis.DataSetEdges
    }
    knowledgeGraphNetwork = new vis.Network(knowledgeGraphContainer, knowledgeGraphNetworkData, knowledgeGraphOptions);
}

/** Set up VisJS for solution graph */
export function initSolutionGraph(div: HTMLElement) {
    let solutionGraphOptions: vis.Options = {
        physics: {
            barnesHut: {
                avoidOverlap: 0.1, // default 0
                springConstant: 0.01,  // default 0.04
                springLength: 50, // default 95
                centralGravity: 0.01, // default 0.3
                gravitationalConstant: -300 // default -2000
            }
        },
        autoResize: true,
        height: "100%"
    }

    let solutionGraphContainer = document.getElementById('solution-graph')
    solutionGraphNetworkData = {
        nodes: new vis.DataSet([]) as vis.DataSetNodes,
        edges: new vis.DataSet([]) as vis.DataSetEdges
    }
    solutionGraphNetwork = new vis.Network(solutionGraphContainer, solutionGraphNetworkData, solutionGraphOptions);
    let solutionGraphCanvas = solutionGraphContainer.getElementsByClassName('vis-network')[0].getElementsByTagName('canvas')[0]
    solutionGraphCanvas.setAttribute('tabindex','1')
    solutionGraphCanvas.addEventListener('keydown', ev => {
        if (ev.key == 'f') {
            solutionGraphNetwork.getSelectedNodes().forEach((value) => {
                solutionGraphNetworkData.nodes.update({
                    id: value,
                    fixed: {
                        x: true,
                        y: true
                    }
                })
            })
        } else if (ev.key == 'r') {
            solutionGraphNetwork.getSelectedNodes().forEach((value) => {
                solutionGraphNetworkData.nodes.update({
                    id: value,
                    fixed: {
                        x: false,
                        y: false
                    }
                })
            })
        }
    });
}

/** Create and connect VisJS nodes for knowledge graph based on response from server */
export function setKnowledgeGraphData(graphData: KnowledgeGraphData) {
    let nodes = knowledgeGraphNetworkData.nodes
    let edges = knowledgeGraphNetworkData.edges

    for (let type of graphData.types) {
        let newNode: vis.Node = {
            label: type.name,
            title: `<pre><code>${type.yaml}</code></pre>`,
            shape: "ellipse",
            color: {
                border: '#64b14b',
                background: '#82e760'
            }
        }
        let [id] = nodes.add(newNode)
        typeToId[type.name] = id as number
    }

    for (let method of graphData.methods) {
        let newNode: vis.Node = {
            label: method.name,
            title: `<pre><code>${method.yaml}</code></pre>`,
            shape: "box",
            color: {
                background: '#e6f0ff'
            }
        }
        let [id] = nodes.add(newNode)
        methodToId[method.name] = id as number
    }

    for (let [name1, name2] of graphData.connections) {
        let fromId = typeToId[name1] ?? methodToId[name1]
        let toId = typeToId[name2] ?? methodToId[name2]

        let newEdge: vis.Edge = {
            from: fromId,
            to: toId,
            arrows: "to",
            color: "black",
            // @ts-ignore
            smooth: {
                enabled: false
            }
        }
        let [id] = edges.add(newEdge)
        edgeIds.push([name1, name2, id as number])
    }

    knowledgeGraphNetwork.stabilize()
}

/** Create and connect VisJS nodes for solution graph based on response from server */
export function setSolutionGraphData(graphData: SolutionGraphData) {
    let nodes = solutionGraphNetworkData.nodes
    let edges = solutionGraphNetworkData.edges

    // Remove the old graph
    edges.clear()
    nodes.clear()

    let nr_start_nodes = graphData.objects.filter(it => it.is_start).length
    let nr_end_nodes = graphData.objects.filter(it => !it.is_start && it.is_end).length

    let start_i = 0  // horizontal index for start nodes
    let end_i = 0  // horizontal index for end nodes

    let H_SPACE = 500  // Horizontal space between fixed nodes
    let V_SPACE = 250  // Mean vertical space between nodes on longest path from start to end

    let maxDistanceToStart = graphData.objects.filter(value => value.is_end).map(value => value.distance_to_start).reduce((a, b) => Math.max(a,b))

    function makeObjectNode(objectData) {
        let newNode: vis.Node = {
            id: objectData.id,
            label: `     ${objectData.name}     `,
            title: `<i>object of type</i> <b>${objectData.type}</b><br>${dictToTooltip(objectData.params)}`,
            shape: "ellipse"
        }

        if (objectData.is_start) {
            newNode.color = {
                border: '#b04a9e',
                background: '#a0d5e5'
            }
            newNode.borderWidth = 4
            newNode.fixed = true
            newNode.x = (start_i - (nr_start_nodes - 1) / 2) * H_SPACE
            start_i++
            newNode.y = 0
        } else if (objectData.is_end) {
            newNode.color = {
                border: '#64b14b',
                background: '#a0d5e5'
            }
            newNode.borderWidth = 4
            newNode.fixed = true
            newNode.x = (end_i - (nr_end_nodes - 1) / 2) * H_SPACE
            end_i++
            newNode.y = maxDistanceToStart * V_SPACE
        } else {
            newNode.color = {
                border: '#a56750',
                background: '#a0d5e5'
            }
            newNode.borderWidth = 4
        }
        return newNode;
    }

    function makeMethodCallNode(methodData) {
        let methodNode: vis.Node = {
            id: methodData.id,
            label: methodData.name,
            shape: "box",
            color: {
                background: '#e6f0ff'
            },
            title: "<i>method call</i>"
        }
        return methodNode;
    }

    function makeInputPortNode(port) {
        let portNode: vis.Node = {
            id: port.id,
            label: port.name,
            title: `<i>${port.tune ? 'tunable input port' : 'input port'}</i><br>${dictToTooltip(port.constraints)}`,
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
        return portNode;
    }

    function makeOutputPortNode(port) {
        let portNode: vis.Node = {
            id: port.id,
            label: port.name,
            title: `<i>output port</i><br>${dictToTooltip(port.constraints)}`,
            shape: "dot",
            size: 4,
            color: {
                border: '#42cb52',
                background: '#bef7c5'
            }
        }
        return portNode;
    }

    function makeArrow(fromId, toId) {
        let arrow: vis.Edge = {
            from: fromId,
            to: toId,
            color: 'black',
            arrows: 'to',
            // @ts-ignore
            smooth: {
                enabled: false
            }
        };
        return arrow
    }

    for (let ao of graphData.objects) {
        let newNode = makeObjectNode(ao);
        nodes.add(newNode)
    }

    for (let method of graphData.methods) {
        let methodNode = makeMethodCallNode(method);
        nodes.add(methodNode)

        for (let port of method.inputs) {
            let portNode = makeInputPortNode(port);
            nodes.add(portNode)

            edges.add(makeArrow(port.id, method.id))
        }

        for (let port of method.outputs) {
            let portNode = makeOutputPortNode(port);
            nodes.add(portNode)
            edges.add(makeArrow(method.id, port.id))
        }
    }

    for (let con of graphData.connections) {
        edges.add(makeArrow(con.fromId, con.toId))
    }

    solutionGraphNetwork.stabilize()
}

/** Convert a param dict to a formatted tooltip */
function dictToTooltip(dict: object): string {
    let tooltip = ""
    for (let [param_name, param_val] of Object.entries(dict)) {
        tooltip += param_name + ": " + param_val + "<br>"
    }

    return tooltip
}

export function stopPhysics() {
    solutionGraphNetwork.setOptions({
        physics: {
            enabled: false
        }
    })
    knowledgeGraphNetwork.setOptions({
        physics: {
            enabled: false
        }
    })
}

export function startPhysics() {
    solutionGraphNetwork.setOptions({
        physics: {
            enabled: true
        }
    })
    knowledgeGraphNetwork.setOptions({
        physics: {
            enabled: true
        }
    })
}

// ----- utility functions for restoring specific layouts using the browser console
export function getSolutionNodePositions() {
    solutionGraphNetwork.storePositions()
    return solutionGraphNetworkData.nodes.map((item) => {
        return {
            id: item.id,
            x: item.x,
            y: item.y
        }
    })
}

export function setSolutionNodePositions(array) {
    for (let entry of array) {
        solutionGraphNetwork.moveNode(entry.id, entry.x, entry.y)
    }
}

export function getKnowledgeNodePositions() {
    knowledgeGraphNetwork.storePositions()
    return knowledgeGraphNetworkData.nodes.map((item) => {
        return {
            id: item.id,
            x: item.x,
            y: item.y
        }
    })
}

export function setKnowledgeNodePositions(array) {
    for (let entry of array) {
        knowledgeGraphNetwork.moveNode(entry.id, entry.x, entry.y)
    }
}
