import numpy as np
import pandas as pd 
import tkinter as tk
import random
import os

from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

# Seed
random.seed(1)
np.random.seed(1)

class CSV():

    @classmethod
    def charger_graph(cls, CSV):
        cls.df  = pd.read_csv(CSV)
        cls.df_to_dict = dict([(i,[a,b]) for i, a,b in zip(cls.df.index, cls.df.x, cls.df.y)])
        return cls.df_to_dict

    @classmethod
    def save_graph(cls, value):
        cls.df = pd.DataFrame.from_dict(data=value, orient='index', columns=['x', 'y'])
        cls.df.to_csv('coord.csv', index=False)

class Lieu():
    
    @classmethod
    def init_lieu(cls, x, y):
        return np.array([x, y])
    
    @classmethod
    def calc_distance(cls, vector1, vector2):
        return np.linalg.norm(vector1 - vector2)

class Route:
    
    @classmethod
    def generation_route(cls, fifo=[0]):
        marquer = []
        while fifo:
            noeud = fifo[0]
            del fifo[0]
            marquer.append(noeud)
            voisin = Graph().plus_proche_voisin(noeud)
            for i in voisin:
                if i not in marquer:
                    fifo.append(i)
                    break
        marquer.append(0)
        way = marquer
        return way

    @classmethod
    def calcul_distance_route(cls, route, matrice):
        cls.score = 0
        for i in range(len(route) - 1):
            cls.pt_start = route[i]
            cls.pt_goal = route[i + 1]
            cls.score += matrice[cls.pt_start, cls.pt_goal]
        return cls.score

class Graph():

    @classmethod
    def creation_points(cls, NB_LIEUX, LARGEUR, HAUTEUR):
        cls.liste_lieux = {}
        for i in range(NB_LIEUX):
            cls.x = random.randint(20, LARGEUR-20)
            cls.y = random.randint(20, HAUTEUR-20)
            cls.liste_lieux[i]=Lieu.init_lieu(cls.x, cls.y)
        return cls.liste_lieux
        
    @classmethod
    def calcul_matrice_cout_od(cls, NB_LIEUX, CSV):
        cls.coord = np.array([v for v in CSV.values()])
        cls.matrix = np.zeros((NB_LIEUX, NB_LIEUX))
        for i in range(len(cls.matrix)):
            for j in range(len(cls.matrix[i])):
                if cls.matrix[i, j] == 0:
                    cls.vecteur1 = cls.coord[i]
                    cls.vecteur2 = cls.coord[j]
                    cls.result = Lieu.calc_distance(cls.vecteur1, cls.vecteur2)
                    cls.matrix[i, j] = cls.result
                    cls.matrix[j, i] = cls.result
        return cls.matrix

    @classmethod
    def plus_proche_voisin(cls, chiffre):
        new_list = list(np.argsort(cls.matrix[chiffre]))
        new_list.remove(chiffre)
        return new_list

class AlgoGen():
    
    @classmethod
    def selection(cls, liste):
        return sorted(liste, key=lambda k: k['score'])[:25]

    @classmethod
    def mutation(cls, mutant):
        index, index2 = random.randint(1, len(mutant)-2), random.randint(1, len(mutant)-2)
        mutant[index], mutant[index2] = mutant[index2], mutant[index]
        return mutant

    @classmethod
    def cross_over(cls, p1, p2):
        index = random.randint(1, len(p1)-2)
        cpt =  round((len(p1[1 : -1]) - index))
        child = p2[index:index+cpt]
        for i in p2[1 : -1]:
            if i not in child:
                child.insert(random.randint(0, len(child)), i)
        child.append(0)
        child.insert(0, 0)
        return child

    @classmethod
    def init_parents(cls, parent):
        cls.population = [parent]
        for _ in range(9):
            cls.population.append([0] + random.sample(parent[1 : -1], k = len(parent[1 : -1])) + [0])
        return cls.population

    @classmethod
    def calc_score(cls, liste, matrice):
        cls.scores_routes = []
        for i in liste:
            cls.scores_routes.append({"route": i, "score": Route.calcul_distance_route(i, matrice)})
        return cls.scores_routes

    @classmethod
    def reproduction(cls, population, matrice):
        cls.enfants = []
        for _ in range(int(os.getenv("TAUX_REPRODUCTION"))):
            cls.enfants.append(cls.cross_over(random.sample(population, k=1)[0]['route'], random.sample(population, k=1)[0]['route']))
        cls.enfants_notes = cls.calc_score(cls.enfants, matrice)
        for enfant in cls.enfants_notes:
            if random.random() > 0.9:
                enfant["route"] = cls.mutation(enfant["route"])
            if enfant["route"] not in [i["route"] for i in population]:
                population.append(enfant)
        return cls.selection(population)

    @classmethod
    def gene_matrice_cout(cls):
        cls.matrice = Graph.calcul_matrice_cout_od(int(os.getenv("NB_LIEUX")), cls.all_points)

    @classmethod
    def gene_route(cls):    
        cls.route = Route.generation_route()
        cls.gene_score_route()

    @classmethod
    def gene_score_route(cls):
        cls.score = Route.calcul_distance_route(cls.route, cls.matrice)

    @classmethod
    def run_algo(cls):
        while True:
            cls.population = cls.reproduction(cls.population, cls.matrice)    
            yield cls.population      

    @classmethod
    def launch(cls, affichage):
        CSV.save_graph(Graph.creation_points(int(os.getenv("NB_LIEUX")), int(os.getenv("LARGEUR")), int(os.getenv("HAUTEUR"))))
        cls.all_points = CSV.charger_graph(os.getenv("CSV"))
        affichage.crea_fenetre(cls.all_points)
        cls.gene_matrice_cout()
        cls.gene_route()
        cls.population = cls.calc_score(cls.init_parents(cls.route), cls.matrice)
        cls.generator = cls.run_algo()
        cls.generator_cnt = 0
        cls.top_score = [{"score": 0, "iter":0}]
        for item in cls.generator:
            if item[0]["score"] < cls.top_score[-1]["score"] or cls.top_score[-1]["score"] == 0:
                cls.top_score.append({"score": item[0]["score"], "iter": cls.generator_cnt})
            affichage.create_line(cls.all_points, item, cls.generator_cnt, cls.top_score)
            affichage.canva.update()
            cls.generator_cnt += 1
        
class Interface():

    @classmethod
    def crea_fenetre(cls, points):
        cls.root = tk.Tk()
        cls.root.title("Challenge Spatial - Groupe 2")
        cls.root.geometry("1200x700")
        cls.root.bind("<Escape>", lambda x: cls.root.destroy())
        cls.canva = tk.Canvas(cls.root, scrollregion=(0,0,500,500), height=os.getenv('HAUTEUR'), width=os.getenv('LARGEUR'))  
        cls.canva.pack(expand=True)
        cls.lab_text = tk.StringVar()
        cls.lab_text.set("Génération n°0")
        cls.lab = tk.Label(cls.root, textvariable=cls.lab_text, fg="#715ec1")
        cls.lab.pack(expand="True")


    @classmethod
    def create_line(cls, points, routes, counter, top_score):
        cls.canva.delete("all")
        cls.lab_text.set(f"Génération n°{counter}\nTop Score: {top_score[-1]['score']} (-{round(top_score[-2]['score'] - top_score[-1]['score'], 3)}) trouvé en {top_score[-1]['iter']} (+ {top_score[-1]['iter'] - top_score[-2]['iter']}) itérations.")
        cnt = 0
        for route in routes:
            if cnt > 0:
                second_layer = cls.canva.create_line([points[i] for i in route["route"]], dash=(5, 2), fill="#CDC9C9")
                cls.canva.tag_lower(second_layer)
                cnt += 1
            else:
                first_layer = cls.canva.create_line([points[i] for i in route["route"]], fill="blue")
                cls.canva.tag_raise(first_layer)
                cnt += 1
        for k, v in points.items():
            if k == 0:
                cls.canva.create_oval(v[0]-12, v[1]-12 , v[0]+12, v[1]+12, fill="red")
            else:
                cls.canva.create_oval(v[0]-12, v[1]-12 , v[0]+12, v[1]+12, fill="#CDC9C9")
            cls.canva.create_text(v[0], v[1], text=str(k))
    
    @classmethod
    def update(cls):
        cls.canva.update()

AlgoGen.launch(Interface)
