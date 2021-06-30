import * as vis from "vis-network/standalone";
import "bootstrap";
import "bootstrap/dist/css/bootstrap.min.css";
import * as monaco from "monaco-editor"
import $ from "jquery";
import {Port, KnowledgeGraphData, SolutionGraphData, fetchKnowledgeGraph, fetchSolutionGraph} from "./methodnet_data";
import {
    getKnowledgeNodePositions,
    getSolutionNodePositions,
    initKnowledgeGraph,
    initSolutionGraph,
    setKnowledgeGraphData, setKnowledgeNodePositions,
    setSolutionGraphData, setSolutionNodePositions, startPhysics,
    stopPhysics
} from "./methodnet_vis";


let startEditor: monaco.editor.IStandaloneCodeEditor
let targetEditor: monaco.editor.IStandaloneCodeEditor

function init() {
    startEditor = monaco.editor.create(document.getElementById("start-editor"), {
        automaticLayout: true,
        minimap: {
            enabled: false
        },
        language: "yaml",
        value:
`start:
  type: ODE
  params:
    Linear: NonLinear
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
  type: TrajectoryTrackingController
`
    })

    initKnowledgeGraph(document.getElementById('knowledge-graph'))
    initSolutionGraph(document.getElementById('solution-graph'))

    loadKnowledgeGraph()
    update()
}

async function loadKnowledgeGraph() {
    let path_components = window.location.pathname.split('/')
    let graphName = path_components[2]

    let graphData = await fetchKnowledgeGraph(graphName)
    setKnowledgeGraphData(graphData)
}

async function update() {
    let path_components = window.location.pathname.split('/')
    let graphName = path_components[2]
    let startYML = startEditor.getValue()
    let targetYML = targetEditor.getValue()

    try {
        let graphData = await fetchSolutionGraph(graphName, startYML, targetYML)
        setSolutionGraphData(graphData)
    } catch (e) {
        let error_text: string = await e.text()
        showError(error_text)
    }
}

function showError(error: string) {
    $('#alert-zone').append(`
            <div class="alert alert-warning alert-dismissible">
                <a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>
                <strong>Error:</strong>
<pre><code>
${error}
</code></pre>
            </div>
        `)
}

function openHelp() {
    document.getElementById("help-popup").classList.remove('help-hidden')
}

function closeHelp() {
    document.getElementById("help-popup").classList.add('help-hidden')
}

// make function globally available
// https://stackoverflow.com/questions/12709074/how-do-you-explicitly-set-a-new-property-on-window-in-typescript
(<any>window).init = init;
(<any>window).update = update;
(<any>window).stopPhysics = stopPhysics;
(<any>window).startPhysics = startPhysics;
(<any>window).getSolutionNodePositions = getSolutionNodePositions;
(<any>window).setSolutionNodePositions = setSolutionNodePositions;
(<any>window).getKnowledgeNodePositions = getKnowledgeNodePositions;
(<any>window).setKnowledgeNodePositions = setKnowledgeNodePositions;
(<any>window).openHelp = openHelp;
(<any>window).closeHelp = closeHelp;
