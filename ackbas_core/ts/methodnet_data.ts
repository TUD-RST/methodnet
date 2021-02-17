export interface Port {
    id: number
    name: string
    constraints: object
    tune?: boolean
}

export interface SolutionGraphData {
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

export interface KnowledgeGraphData {
    types: {
        name: string,
        yaml: string
    }[]
    methods: {
        name: string
        description: string | null,
        yaml: string
    }[]
    connections: [string, string][]
}

export async function fetchKnowledgeGraph(graphName: string): Promise<KnowledgeGraphData> {
    let response = await fetch('/kg/' + graphName)
    return await response.json() as KnowledgeGraphData
}

export async function fetchSolutionGraph(graphName: string, startYML: string, targetYML: string): Promise<SolutionGraphData> {
    let response = await fetch('/s', {
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

    if (!response.ok)
        throw response;
    return await response.json() as SolutionGraphData;
}
