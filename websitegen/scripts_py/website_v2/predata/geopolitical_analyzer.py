# geopolitical_analyzer.py
from nlp_utils import analyze_text
import pandas as pd
import networkx as nx
import pycountry
from collections import defaultdict
import matplotlib.pyplot as plt

class GeopoliticalAnalyzer:
    def __init__(self):
        self.country_data = defaultdict(lambda: pd.DataFrame())
        self.relationship_graph = nx.DiGraph()
        self.entity_graph = nx.Graph()

    def process_headlines(self, headlines):
        for article in headlines:
            analysis = analyze_text(article["title"])
            date = article["date"]
            entities = self._extract_entities(analysis["entities"])
            relationships = self._extract_relationships(analysis["relationships"])
            self._update_country_data(entities, relationships, date)
            self._update_relationship_graph(entities, relationships)
            self._update_entity_graph(entities, relationships)

    def _extract_entities(self, entities):
        return [(self._normalize_entity(ent[0], ent[1]), ent[1]) for ent in entities]

    def _extract_relationships(self, relationships):
        return relationships

    def _normalize_entity(self, name, ent_type):
        if ent_type == "GPE":
            try:
                return pycountry.countries.lookup(name).alpha_3
            except:
                return name
        return name.lower().strip()

    def _update_country_data(self, entities, relationships, date):
        countries = {e[0] for e in entities if len(e[0]) == 3}
        for country in countries:
            for rel in relationships:
                if rel["subject"] == country or rel["object"] == country:
                    record = {
                        "date": date,
                        "event": rel["verb"],
                        "count": 1,
                        "target": rel["object"] if rel["subject"] == country else rel["subject"]
                    }
                    self.country_data[country] = pd.concat([
                        self.country_data[country],
                        pd.DataFrame([record])
                    ])

    def _update_relationship_graph(self, entities, relationships):
        for rel in relationships:
            subj = self._normalize_entity(rel["subject"], "GPE")
            obj = self._normalize_entity(rel["object"], "GPE")
            if subj != obj:
                if self.relationship_graph.has_edge(subj, obj):
                    self.relationship_graph[subj][obj]["weight"] += 1
                    self.relationship_graph[subj][obj]["verbs"].add(rel["verb"])
                else:
                    self.relationship_graph.add_edge(
                        subj, obj,
                        weight=1,
                        verbs={rel["verb"]},
                        type="country_relation"
                    )

    def _update_entity_graph(self, entities, relationships):
        for ent, ent_type in entities:
            self.entity_graph.add_node(ent, type=ent_type)
        for rel in relationships:
            subj = self._normalize_entity(rel["subject"], "GPE")
            obj = self._normalize_entity(rel["object"], "GPE")
            if subj in self.entity_graph and obj in self.entity_graph:
                self.entity_graph.add_edge(subj, obj, verb=rel["verb"])

    def visualize_relationships(self, min_weight=2):
        plt.figure(figsize=(15, 10))
        edges = [(u, v) for (u, v, d) in self.relationship_graph.edges(data=True) if d["weight"] >= min_weight]
        pos = nx.spring_layout(self.relationship_graph)
        nx.draw_networkx_nodes(self.relationship_graph, pos, node_size=500, node_color="lightblue")
        nx.draw_networkx_edges(self.relationship_graph, pos, edgelist=edges, width=[d["weight"]*0.5 for (u,v,d) in self.relationship_graph.edges(data=True) if (u,v) in edges], edge_color="gray", arrowsize=20)
        edge_labels = {(u, v): ", ".join(d["verbs"])[:15] + "..." for u, v, d in self.relationship_graph.edges(data=True) if (u,v) in edges}
        nx.draw_networkx_edge_labels(self.relationship_graph, pos, edge_labels=edge_labels, font_size=8)
        nx.draw_networkx_labels(self.relationship_graph, pos, font_size=10, font_weight="bold")
        plt.title("Geopolitical Relationship Network")
        plt.axis("off")
        plt.tight_layout()
        plt.show()

    def visualize_entity_network(self):
        plt.figure(figsize=(15, 10))
        node_colors = []
        for node in self.entity_graph.nodes():
            if len(node) == 3:
                node_colors.append("lightblue")
            elif self.entity_graph.nodes[node]["type"] == "ORG":
                node_colors.append("lightgreen")
            else:
                node_colors.append("pink")
        pos = nx.spring_layout(self.entity_graph)
        nx.draw(self.entity_graph, pos, with_labels=True, node_size=500, node_color=node_colors, font_size=8, edge_color="gray")
        plt.title("Entity Relationship Network")
        plt.axis("off")
        plt.show()
