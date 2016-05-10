CC=g++-4.7
CCOPTS=-O3 -march=core2 -std=c++11 -pthread
INCLUDEDIR=-Isrc/ -I/usr/local/include
LIBDIR=-L/usr/local/lib
LIBS=-lccn -lcrypto -lrt

all: build

build:
	$(CC) $(CCOPTS) $(INCLUDEDIR) -c src/Buffer.cpp
	$(CC) $(CCOPTS) $(INCLUDEDIR) -c src/CCNComm.cpp
	$(CC) $(CCOPTS) $(INCLUDEDIR) -c src/CCNRelations.cpp
	$(CC) $(CCOPTS) $(INCLUDEDIR) -c src/Experiment.cpp
	$(CC) $(CCOPTS) $(INCLUDEDIR) -c src/Threads.cpp
	$(CC) $(CCOPTS) $(INCLUDEDIR) -c src/MetaBuffer.cpp
	$(CC) $(CCOPTS) $(INCLUDEDIR) -c BasicStreamExperiment.cpp
	$(CC) $(CCOPTS) $(INCLUDEDIR) -c RelationStreamExperiment.cpp
	$(CC) $(CCOPTS) $(LIBDIR) -o BasicStreamExperiment Buffer.o MetaBuffer.o CCNComm.o CCNRelations.o Experiment.o Threads.o BasicStreamExperiment.o $(LIBS)
	$(CC) $(CCOPTS) $(LIBDIR) -o RelationStreamExperiment Buffer.o MetaBuffer.o CCNComm.o CCNRelations.o Experiment.o Threads.o RelationStreamExperiment.o $(LIBS)

clean:
	rm *.o BasicStreamExperiment RelationStreamExperiment
