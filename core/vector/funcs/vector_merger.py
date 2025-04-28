from typing import List

from core.vector.vector import Vector


class VectorMerger:    
    @staticmethod
    def merge(vector_list: List[Vector]) -> Vector:
        if not vector_list:
            raise ValueError('vector_list is empty')
        
        if len(vector_list) == 1:
            return vector_list[0]
        
        #check handler
        handler = vector_list[0].handler
        for vector in vector_list:
            if vector.handler != handler:
                raise ValueError('All vectors must have the same handler')
                
        merged_vector = Vector.like(vector_list[0])

        for vector in vector_list:
            from_layer = vector.raw.GetLayer()
            merged_layer = merged_vector.raw.GetLayer()
            merged_vector.handler.copy_features(merged_layer, from_layer)
        
        return merged_vector
