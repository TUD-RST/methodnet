import { Network, DataSet } from "vis-network/standalone";

function initGraph() {
    // create an array with nodes
    let nodes = new DataSet([
        {id: 1, label: 'Node 1'},
        {id: 2, label: 'Node 2'},
        {id: 3, label: 'Node 3'},
        {id: 4, label: 'Node 4'},
        {id: 5, label: 'Node 5'}
    ]);

    // create an array with edges
    let edges = new DataSet([
        {id: 1, from: 1, to: 3},
        {id: 2, from: 1, to: 2},
        {id: 3, from: 2, to: 4},
        {id: 4, from: 2, to: 5},
        {id: 5, from: 3, to: 3}
    ]);

    // create a network
    let container = document.getElementById('mynetwork');
    let data = {
        nodes: nodes,
        edges: edges
    };
    let options = {};
    let network = new Network(container, data, options);
}

// make function globally available
// https://stackoverflow.com/questions/12709074/how-do-you-explicitly-set-a-new-property-on-window-in-typescript
(<any>window).initGraph = initGraph