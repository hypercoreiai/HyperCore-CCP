#include <cstdlib>
#include <iostream>
#include <vector>

// deliberately leaks a vector so valgrind has something to find
static std::vector<int>* make_weights(int n) {
    std::vector<int>* w = new std::vector<int>(n);
    for (int i = 0; i < n; ++i) {
        (*w)[i] = i * i;
    }
    return w;
}

int main(int argc, char** argv) {
    int n = argc > 1 ? std::atoi(argv[1]) : 5;
    std::vector<int>* w = make_weights(n);
    int total = 0;
    for (int i = 0; i < n; ++i) {
        total += (*w)[i];
    }
    std::cout << "total=" << total << "\n";
    return 0;
}
