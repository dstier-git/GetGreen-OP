# Define a simple class called Dog


class Dog:
    # Constructor 
   def __init__(self, name, age):
    self.name = name
    self.age = age

   def bark(self):
    print(f"{self.name} says: Woof!")

   def have_birthday(self):
    self.age += 1
    print(f"Happy birthday, {self.name}! You are now {self.age} years old.")

dog = Dog("Dylan", 19)
dog.bark()
dog.have_birthday()
